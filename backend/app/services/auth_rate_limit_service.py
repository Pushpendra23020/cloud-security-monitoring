import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.auth_rate_limit import AuthRateLimit


class RateLimitExceeded(ValueError):
    def __init__(self, retry_after: int):
        self.retry_after = max(retry_after, 1)
        super().__init__("Too many authentication attempts.")


class AuthenticationRateLimitService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_allowed(self, *, client_ip: str, principal: str) -> None:
        now = datetime.now(timezone.utc)
        for scope, value in self._scopes(client_ip, principal):
            entry = self.db.get(AuthRateLimit, self._key(scope, value))
            if entry and entry.blocked_until and entry.blocked_until > now:
                raise RateLimitExceeded(
                    int((entry.blocked_until - now).total_seconds()) + 1
                )

    def record_failure(self, *, client_ip: str, principal: str) -> None:
        now = datetime.now(timezone.utc)
        for scope, value in self._scopes(client_ip, principal):
            maximum = (
                settings.AUTH_RATE_LIMIT_IP_ATTEMPTS
                if scope == "ip"
                else settings.AUTH_RATE_LIMIT_PRINCIPAL_ATTEMPTS
            )
            key = self._key(scope, value)
            self.db.execute(
                insert(AuthRateLimit)
                .values(
                    key=key,
                    scope=scope,
                    attempts=0,
                    window_started_at=now,
                    updated_at=now,
                )
                .on_conflict_do_nothing(index_elements=["key"])
            )
            entry = self.db.scalar(
                select(AuthRateLimit)
                .where(AuthRateLimit.key == key)
                .with_for_update()
            )
            window_age = (now - entry.window_started_at).total_seconds()
            if window_age >= settings.AUTH_RATE_LIMIT_WINDOW_SECONDS:
                entry.attempts = 0
                entry.window_started_at = now
                entry.blocked_until = None
            entry.attempts += 1
            entry.updated_at = now
            if entry.attempts >= maximum:
                entry.blocked_until = now + timedelta(
                    seconds=settings.AUTH_RATE_LIMIT_BLOCK_SECONDS
                )
        self.db.commit()

    def clear_principal(self, *, client_ip: str, principal: str) -> None:
        scope = "principal"
        value = f"{client_ip}|{principal.strip().lower()}"
        self.db.execute(
            delete(AuthRateLimit).where(AuthRateLimit.key == self._key(scope, value))
        )
        self.db.commit()

    @staticmethod
    def _scopes(client_ip: str, principal: str) -> tuple[tuple[str, str], ...]:
        normalized = principal.strip().lower()
        return (
            ("ip", client_ip),
            ("principal", f"{client_ip}|{normalized}"),
        )

    @staticmethod
    def _key(scope: str, value: str) -> str:
        return hmac.new(
            settings.SECRET_KEY.encode(),
            f"{scope}:{value}".encode(),
            hashlib.sha256,
        ).hexdigest()
