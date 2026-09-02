from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.auth_session import AuthSession


class AuthSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, session_id: str) -> AuthSession | None:
        return self.db.get(AuthSession, session_id)

    def get_for_update(self, session_id: str) -> AuthSession | None:
        return self.db.scalar(
            select(AuthSession)
            .where(AuthSession.id == session_id)
            .with_for_update()
        )

    def list_active_for_user(self, user_id: int) -> list[AuthSession]:
        now = datetime.now(timezone.utc)
        return list(
            self.db.scalars(
                select(AuthSession)
                .where(
                    AuthSession.user_id == user_id,
                    AuthSession.revoked_at.is_(None),
                    AuthSession.expires_at > now,
                )
                .order_by(AuthSession.last_seen_at.desc())
            )
        )

    def revoke(self, session: AuthSession, reason: str) -> None:
        if session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            session.revoke_reason = reason
            self.db.commit()

    def revoke_all_for_user(self, user_id: int, reason: str) -> int:
        sessions = self.list_active_for_user(user_id)
        now = datetime.now(timezone.utc)
        for session in sessions:
            session.revoked_at = now
            session.revoke_reason = reason
        self.db.commit()
        return len(sessions)

    def revoke_all_except(
        self,
        user_id: int,
        session_id: str | None,
        reason: str,
    ) -> int:
        sessions = [
            session
            for session in self.list_active_for_user(user_id)
            if session.id != session_id
        ]
        now = datetime.now(timezone.utc)
        for session in sessions:
            session.revoked_at = now
            session.revoke_reason = reason
        self.db.commit()
        return len(sessions)
