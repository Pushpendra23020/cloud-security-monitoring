from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.security import TokenError, decode_access_token
from app.database.models.audit_log import AuditLog
from app.repositories.user_repository import UserRepository
from app.database.session import SessionLocal


class AuditMiddleware(BaseHTTPMiddleware):
    """Persist authenticated state-changing API activity."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if (
            settings.AUTH_ENABLED
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and request.url.path.startswith("/api/v1/")
        ):
            username = self._username(request)
            if username:
                with SessionLocal() as db:
                    db.add(
                        AuditLog(
                            action=f"{request.method} {request.url.path}",
                            user=username,
                            method=request.method,
                            path=request.url.path,
                            status_code=response.status_code,
                            client_ip=request.client.host if request.client else None,
                        )
                    )
                    db.commit()
        return response

    @staticmethod
    def _username(request: Request) -> str | None:
        value = request.headers.get("Authorization", "")
        if not value.startswith("Bearer "):
            return None
        try:
            return str(decode_access_token(value[7:]).get("username"))
        except TokenError:
            return None


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Require an active bearer-token user for protected Phase 10 APIs."""

    PUBLIC_PATHS = {
        "/api/v1/auth/status",
        "/api/v1/auth/login",
        "/api/v1/health",
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
                if user.role == "viewer" and request.method not in {"GET", "HEAD"}:
                    return JSONResponse(
                        {"detail": "Viewer accounts have read-only access."},
                        status_code=403,
                    )
        except (TokenError, ValueError, KeyError):
            return self._unauthorized("Invalid or expired access token.")
        return await call_next(request)

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(
            {"detail": detail},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
