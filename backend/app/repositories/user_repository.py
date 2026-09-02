from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.user import User
from app.config import settings


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(
            select(User).where(User.username == username)
        )

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_oidc_identity(self, issuer: str, subject: str) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.oidc_issuer == issuer,
                User.oidc_subject == subject,
            )
        )

    def list(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.username)))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def record_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()

    def record_failed_login(self, user: User) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.AUTH_MAX_FAILED_LOGINS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.AUTH_LOCKOUT_MINUTES
            )
        self.db.commit()

    @staticmethod
    def is_locked(user: User) -> bool:
        return bool(
            user.locked_until
            and user.locked_until > datetime.now(timezone.utc)
        )
