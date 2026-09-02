from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models.organization import OrganizationMembership
from app.database.models.user import User
from app.database.models.audit_log import AuditLog
from app.database.session import get_db
from app.dependencies import CurrentOrganizationId, require_roles
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    AuditLogResponse,
    OidcIdentityResponse,
    OidcIdentityUpdate,
    UserCreate,
    UserResponse,
    UserStatusUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])
admin_required = require_roles("admin")


def _member_response(user: User, membership: OrganizationMembership) -> UserResponse:
    return UserResponse.model_validate(user).model_copy(
        update={"role": membership.role, "is_active": membership.is_active}
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    organization_id: CurrentOrganizationId,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> list[AuditLog]:
    safe_limit = min(max(limit, 1), 500)
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .limit(safe_limit)
        )
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> list[UserResponse]:
    return [
        _member_response(user, membership)
        for user, membership in OrganizationRepository(db).list_members(organization_id)
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreate,
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> UserResponse:
    repository = UserRepository(db)
    if repository.get_by_username(request.username) or repository.get_by_email(request.email):
        raise HTTPException(status_code=409, detail="Username or email already exists.")
    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.flush()
    membership = OrganizationMembership(
        organization_id=organization_id,
        user_id=user.id,
        role=request.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(membership)
    return _member_response(user, membership)


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    request: UserStatusUpdate,
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_required),
) -> UserResponse:
    if actor.id == user_id and not request.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself.")
    organization_repository = OrganizationRepository(db)
    membership = organization_repository.get_membership(
        user_id,
        organization_id,
        active_only=False,
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if (
        membership.role == "admin"
        and membership.is_active
        and not request.is_active
        and organization_repository.count_active_admins(organization_id) <= 1
    ):
        raise HTTPException(
            status_code=400,
            detail="The last active administrator cannot be deactivated.",
        )
    membership.is_active = request.is_active
    db.commit()
    user = UserRepository(db).get_by_id(user_id)
    db.refresh(user)
    db.refresh(membership)
    return _member_response(user, membership)


@router.put("/{user_id}/oidc-identity", response_model=OidcIdentityResponse)
def link_oidc_identity(
    user_id: int,
    request: OidcIdentityUpdate,
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> OidcIdentityResponse:
    membership = OrganizationRepository(db).get_membership(
        user_id,
        organization_id,
        active_only=False,
    )
    user = UserRepository(db).get_by_id(user_id) if membership else None
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    existing = UserRepository(db).get_by_oidc_identity(
        request.issuer.rstrip("/"),
        request.subject,
    )
    if existing is not None and existing.id != user.id:
        raise HTTPException(status_code=409, detail="OIDC identity is already linked.")
    user.oidc_issuer = request.issuer.rstrip("/")
    user.oidc_subject = request.subject
    db.commit()
    return OidcIdentityResponse(
        user_id=user.id,
        issuer=user.oidc_issuer,
        subject=user.oidc_subject,
    )


@router.delete("/{user_id}/oidc-identity", status_code=status.HTTP_204_NO_CONTENT)
def unlink_oidc_identity(
    user_id: int,
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> None:
    membership = OrganizationRepository(db).get_membership(
        user_id,
        organization_id,
        active_only=False,
    )
    user = UserRepository(db).get_by_id(user_id) if membership else None
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.oidc_issuer = None
    user.oidc_subject = None
    db.commit()
