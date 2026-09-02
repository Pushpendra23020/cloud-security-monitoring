import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.mfa import MfaChallenge, MfaRecoveryCode
from app.database.models.user import User


class MfaError(ValueError):
    pass


class MfaService:
    def __init__(self, db: Session):
        self.db = db

    def begin_setup(self, user: User) -> tuple[str, str]:
        if user.mfa_enabled:
            raise MfaError("MFA is already enabled.")
        secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
        user.mfa_secret_encrypted = self._encrypt_secret(user.id, secret)
        user.mfa_last_used_step = None
        self.db.commit()
        label = quote(f"{settings.AUTH_MFA_ISSUER}:{user.email}")
        issuer = quote(settings.AUTH_MFA_ISSUER)
        uri = (
            f"otpauth://totp/{label}?secret={secret}&issuer={issuer}"
            "&algorithm=SHA1&digits=6&period=30"
        )
        return secret, uri

    def create_challenge(self, user_id: int) -> MfaChallenge:
        now = datetime.now(timezone.utc)
        challenge = MfaChallenge(
            id=str(uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(minutes=settings.AUTH_MFA_CHALLENGE_MINUTES),
        )
        self.db.add(challenge)
        self.db.commit()
        return challenge

    def lock_active_challenge(
        self,
        challenge_id: str,
        user_id: int,
    ) -> MfaChallenge | None:
        challenge = self.db.scalar(
            select(MfaChallenge)
            .where(MfaChallenge.id == challenge_id)
            .with_for_update()
        )
        now = datetime.now(timezone.utc)
        if (
            challenge is None
            or challenge.user_id != user_id
            or challenge.consumed_at is not None
            or challenge.expires_at <= now
        ):
            return None
        return challenge

    def consume_challenge(self, challenge: MfaChallenge) -> None:
        challenge.consumed_at = datetime.now(timezone.utc)
        self.db.commit()

    def enable(self, user: User, code: str) -> list[str]:
        if user.mfa_enabled:
            raise MfaError("MFA is already enabled.")
        if not user.mfa_secret_encrypted:
            raise MfaError("Start MFA setup first.")
        step = self._verify_totp(user, code)
        if step is None:
            raise MfaError("Invalid authentication code.")
        user.mfa_enabled = True
        user.mfa_last_used_step = step
        recovery_codes = self._replace_recovery_codes(user.id)
        self.db.commit()
        return recovery_codes

    def verify(self, user: User, code: str, *, commit: bool = True) -> bool:
        if not user.mfa_enabled or not user.mfa_secret_encrypted:
            return False
        normalized = self._normalize_code(code)
        if normalized.isdigit() and len(normalized) == 6:
            step = self._verify_totp(user, normalized)
            if step is None:
                return False
            user.mfa_last_used_step = step
            if commit:
                self.db.commit()
            return True

        code_hash = self._hash_recovery_code(normalized)
        recovery = self.db.scalar(
            select(MfaRecoveryCode).where(
                MfaRecoveryCode.user_id == user.id,
                MfaRecoveryCode.code_hash == code_hash,
                MfaRecoveryCode.used_at.is_(None),
            )
        )
        if recovery is None:
            return False
        recovery.used_at = datetime.now(timezone.utc)
        if commit:
            self.db.commit()
        return True

    def disable(self, user: User) -> None:
        user.mfa_enabled = False
        user.mfa_secret_encrypted = None
        user.mfa_last_used_step = None
        self.db.execute(
            delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id)
        )
        self.db.commit()

    def regenerate_recovery_codes(self, user: User) -> list[str]:
        if not user.mfa_enabled:
            raise MfaError("MFA is not enabled.")
        codes = self._replace_recovery_codes(user.id)
        self.db.commit()
        return codes

    def recovery_codes_remaining(self, user_id: int) -> int:
        return int(
            self.db.scalar(
                select(func.count(MfaRecoveryCode.id)).where(
                    MfaRecoveryCode.user_id == user_id,
                    MfaRecoveryCode.used_at.is_(None),
                )
            )
            or 0
        )

    def _verify_totp(self, user: User, code: str) -> int | None:
        try:
            secret = self._decrypt_secret(user.id, user.mfa_secret_encrypted or "")
        except (ValueError, MfaError):
            return None
        current_step = int(time.time()) // 30
        for step in range(current_step - 1, current_step + 2):
            expected = self._totp(secret, step)
            if hmac.compare_digest(expected, code):
                if user.mfa_last_used_step is not None and step <= user.mfa_last_used_step:
                    return None
                return step
        return None

    def _replace_recovery_codes(self, user_id: int) -> list[str]:
        self.db.execute(
            delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user_id)
        )
        codes = [self._new_recovery_code() for _ in range(10)]
        self.db.add_all(
            MfaRecoveryCode(
                user_id=user_id,
                code_hash=self._hash_recovery_code(code),
            )
            for code in codes
        )
        return codes

    def _encrypt_secret(self, user_id: int, secret: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self._encryption_key()).encrypt(
            nonce,
            secret.encode(),
            f"mfa:user:{user_id}".encode(),
        )
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def _decrypt_secret(self, user_id: int, encrypted: str) -> str:
        try:
            payload = base64.urlsafe_b64decode(encrypted.encode())
            return AESGCM(self._encryption_key()).decrypt(
                payload[:12],
                payload[12:],
                f"mfa:user:{user_id}".encode(),
            ).decode()
        except Exception as exc:
            raise MfaError("MFA secret cannot be decrypted.") from exc

    @staticmethod
    def _encryption_key() -> bytes:
        material = settings.AUTH_MFA_ENCRYPTION_KEY or settings.SECRET_KEY
        return hashlib.sha256(material.encode()).digest()

    @classmethod
    def _hash_recovery_code(cls, code: str) -> str:
        return hmac.new(
            cls._encryption_key(),
            cls._normalize_code(code).encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _normalize_code(code: str) -> str:
        return "".join(character for character in code.upper() if character.isalnum())

    @staticmethod
    def _new_recovery_code() -> str:
        raw = secrets.token_hex(6).upper()
        return "-".join(raw[index:index + 4] for index in range(0, 12, 4))

    @staticmethod
    def _totp(secret: str, step: int) -> str:
        padding = "=" * ((8 - len(secret) % 8) % 8)
        key = base64.b32decode(secret + padding, casefold=True)
        digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        return f"{value % 1_000_000:06d}"
