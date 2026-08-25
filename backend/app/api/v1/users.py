from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models.user import User
from app.database.models.audit_log import AuditLog
from app.database.session import get_db
from app.dependencies import require_roles
from app.repositories.user_repository import UserRepository
from app.schemas.user import AuditLogResponse, UserCreate, UserResponse, UserStatusUpdate

router = APIRouter(prefix="/users", tags=["Users"])
admin_required = require_roles("admin")


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> list[AuditLog]:
    safe_limit = min(max(limit, 1), 500)
    return list(
        db.scalars(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(safe_limit)
        )
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> list[User]:
    return UserRepository(db).list()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
) -> User:
    repository = UserRepository(db)
    if repository.get_by_username(request.username) or repository.get_by_email(request.email):
        raise HTTPException(status_code=409, detail="Username or email already exists.")
    return repository.add(
        User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            role=request.role,
        )
    )


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    request: UserStatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(admin_required),
) -> User:
    if actor.id == user_id and not request.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself.")
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = request.is_active
    db.commit()
    db.refresh(user)
    return user
