import hmac
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import create_refresh_token, hash_refresh_token
from app.database.models.auth_session import AuthSession
from app.repositories.auth_session_repository import AuthSessionRepository


class SessionAuthenticationError(ValueError):
    pass


class RefreshTokenReuseError(SessionAuthenticationError):
    pass


class AuthSessionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuthSessionRepository(db)

    def create(
        self,
        *,
        user_id: int,
        organization_id: int,
        membership_id: int,
        user_agent: str | None,
        client_ip: str | None,
    ) -> tuple[AuthSession, str]:
        session_id = str(uuid4())
        raw_token = create_refresh_token(session_id)
        now = datetime.now(timezone.utc)
        session = AuthSession(
            id=session_id,
            user_id=user_id,
            organization_id=organization_id,
            membership_id=membership_id,
            refresh_token_hash=hash_refresh_token(raw_token),
            user_agent=(user_agent or "")[:500] or None,
            client_ip=(client_ip or "")[:64] or None,
            created_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(days=settings.AUTH_SESSION_EXPIRE_DAYS),
        )
        self.db.add(session)
        self.db.commit()
        return session, raw_token

    def rotate(self, raw_token: str) -> tuple[AuthSession, str]:
        session = self._session_from_token(raw_token)
        presented_hash = hash_refresh_token(raw_token)
        if session.previous_refresh_token_hash and hmac.compare_digest(
            presented_hash,
            session.previous_refresh_token_hash,
        ):
            self.repository.revoke(session, "refresh_token_reuse")
            raise RefreshTokenReuseError("Refresh token reuse detected.")
        if not hmac.compare_digest(presented_hash, session.refresh_token_hash):
            raise SessionAuthenticationError("Invalid refresh token.")
        self._require_active(session)

        replacement = create_refresh_token(session.id)
        session.previous_refresh_token_hash = session.refresh_token_hash
        session.refresh_token_hash = hash_refresh_token(replacement)
        session.last_seen_at = datetime.now(timezone.utc)
        self.db.commit()
        return session, replacement

    def validate_access(self, session_id: str, user_id: int) -> AuthSession:
        session = self.repository.get(session_id)
        if session is None or session.user_id != user_id:
            raise SessionAuthenticationError("Session is unavailable.")
        self._require_active(session)
        return session

    def revoke_with_token(self, raw_token: str, reason: str = "logout") -> None:
        try:
            session = self._session_from_token(raw_token)
        except SessionAuthenticationError:
            return
        presented_hash = hash_refresh_token(raw_token)
        valid_hashes = {
            session.refresh_token_hash,
            session.previous_refresh_token_hash,
        }
        if any(
            value and hmac.compare_digest(presented_hash, value)
            for value in valid_hashes
        ):
            self.repository.revoke(session, reason)

    def _session_from_token(self, raw_token: str) -> AuthSession:
        try:
            session_id, secret = raw_token.split(".", 1)
        except (AttributeError, ValueError) as exc:
            raise SessionAuthenticationError("Invalid refresh token.") from exc
        if not session_id or not secret:
            raise SessionAuthenticationError("Invalid refresh token.")
        session = self.repository.get_for_update(session_id)
        if session is None:
            raise SessionAuthenticationError("Invalid refresh token.")
        return session

    @staticmethod
    def _require_active(session: AuthSession) -> None:
        now = datetime.now(timezone.utc)
        if session.revoked_at is not None or session.expires_at <= now:
            raise SessionAuthenticationError("Session is inactive.")
