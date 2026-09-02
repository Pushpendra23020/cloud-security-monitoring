from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import TokenError, decode_access_token
from app.core.tenancy import DEFAULT_ORGANIZATION_ID, TenantContext
from app.database.models.user import User
from app.database.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.auth_session_service import (
    AuthSessionService,
    SessionAuthenticationError,
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_tenant(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantContext:
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is disabled.",
        )
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        user = UserRepository(db).get_by_id(int(payload["sub"]))
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
        membership = OrganizationRepository(db).get_membership(user.id, organization_id) if user else None
        organization = OrganizationRepository(db).get(organization_id) if membership else None
    except (TokenError, SessionAuthenticationError, ValueError, KeyError, TypeError):
        user = None
        membership = None
        organization = None
        auth_session = None
        session_id = None
    if (
        user is None
        or not user.is_active
        or membership is None
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive user.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TenantContext(
        user=user,
        organization_id=membership.organization_id,
        role=membership.role,
        membership_id=membership.id,
        session_id=session_id,
    )


CurrentTenant = Annotated[TenantContext, Depends(get_current_tenant)]


def get_current_user(context: CurrentTenant) -> User:
    return context.user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str):
    def dependency(context: CurrentTenant) -> User:
        if context.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return context.user
    return dependency


def get_current_organization_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> int:
    # Authentication is intentionally optional for legacy local/test mode. Such
    # deployments remain a single trusted workspace; production enables auth.
    if not settings.AUTH_ENABLED:
        return DEFAULT_ORGANIZATION_ID
    return get_current_tenant(credentials, db).organization_id


CurrentOrganizationId = Annotated[int, Depends(get_current_organization_id)]
