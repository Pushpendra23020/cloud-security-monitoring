from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.security import TokenError, decode_access_token
from app.database.models.audit_log import AuditLog
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.database.session import SessionLocal, set_tenant_context
from app.services.auth_session_service import (
    AuthSessionService,
    SessionAuthenticationError,
)
from app.utils.client_ip import resolve_client_ip


class AuditMiddleware(BaseHTTPMiddleware):
    """Persist authenticated state-changing API activity."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if (
            settings.AUTH_ENABLED
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and request.url.path.startswith("/api/v1/")
        ):
            username = getattr(request.state, "username", None)
            organization_id = getattr(request.state, "organization_id", None)
            if username and organization_id is not None:
                with SessionLocal() as db:
                    set_tenant_context(db, organization_id)
                    db.add(
                        AuditLog(
                            organization_id=organization_id,
                            action=f"{request.method} {request.url.path}",
                            user=username,
                            method=request.method,
                            path=request.url.path,
                            status_code=response.status_code,
                            client_ip=resolve_client_ip(request),
                        )
                    )
                    db.commit()
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Require an active bearer-token user for protected Phase 10 APIs."""

    PUBLIC_PATHS = {
        "/api/v1/auth/status",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/mfa/verify",
        "/api/v1/auth/oidc/start",
        "/api/v1/auth/oidc/callback",
        "/api/v1/health",
    }
    VIEWER_SELF_SERVICE_PATHS = {
        "/api/v1/auth/switch-organization",
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if (
            not settings.AUTH_ENABLED
            or not path.startswith("/api/v1/")
            or path in self.PUBLIC_PATHS
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        value = request.headers.get("Authorization", "")
        if not value.startswith("Bearer "):
            return self._unauthorized("Authentication required.")
        try:
            payload = decode_access_token(value[7:])
            with SessionLocal() as db:
                user = UserRepository(db).get_by_id(int(payload["sub"]))
                if user is None or not user.is_active:
                    return self._unauthorized("Invalid or inactive user.")
                organization_id = int(payload["org_id"])
                membership_id = int(payload["membership_id"])
                session_id = payload.get("sid")
                auth_session = None
                if session_id:
                    auth_session = AuthSessionService(db).validate_access(
                        session_id,
                        user.id if user else -1,
                    )
                elif settings.ENVIRONMENT.lower() != "test":
                    raise SessionAuthenticationError("Session identifier required.")
                organization_repository = OrganizationRepository(db)
                membership = organization_repository.get_membership(user.id, organization_id)
                organization = organization_repository.get(organization_id)
                if (
                    membership is None
                    or membership.id != membership_id
                    or organization is None
                    or not organization.is_active
                    or (
                        auth_session is not None
                        and (
                            auth_session.organization_id != organization_id
                            or auth_session.membership_id != membership_id
                        )
                    )
                ):
                    return self._unauthorized("Invalid or inactive organization membership.")
                request.state.user_id = user.id
                request.state.username = user.username
                request.state.organization_id = organization_id
                request.state.membership_role = membership.role
                request.state.session_id = session_id
                if (
                    membership.role not in {"admin", "analyst"}
                    and request.method not in {"GET", "HEAD"}
                    and path not in self.VIEWER_SELF_SERVICE_PATHS
                    and not path.startswith("/api/v1/auth/sessions/")
                    and not path.startswith("/api/v1/auth/mfa/")
                ):
                    return JSONResponse(
                        {"detail": "Viewer accounts have read-only access."},
                        status_code=403,
                    )
        except (
            TokenError,
            SessionAuthenticationError,
            ValueError,
            KeyError,
            TypeError,
        ):
            return self._unauthorized("Invalid or expired access token.")
        return await call_next(request)

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(
            {"detail": detail},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
