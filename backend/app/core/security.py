import base64
import hashlib
import hmac
import os
import secrets
import string
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from app.config import settings


class TokenError(ValueError):
    pass


def validate_password_strength(password: str) -> None:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    if len(password) > 1024:
        raise ValueError("Password must contain at most 1024 characters.")
    requirements = (
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
        any(character in string.punctuation for character in password),
    )
    if not all(requirements):
        raise ValueError(
            "Password must include uppercase, lowercase, numeric, and special characters."
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return "pbkdf2_sha256$600000$%s$%s" % (
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_value, digest_value = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode())
        expected = base64.urlsafe_b64decode(digest_value.encode())
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    organization_id: int,
    membership_id: int,
    session_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "org_id": organization_id,
        "membership_id": membership_id,
        "sid": session_id,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(session_id: str) -> str:
    return f"{session_id}.{secrets.token_urlsafe(48)}"


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access" or not payload.get("sub"):
            raise TokenError("Invalid access token.")
        return payload
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired access token.") from exc


def create_mfa_challenge_token(
    challenge_id: str,
    user_id: int,
    organization_id: int,
    membership_id: int,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "org_id": organization_id,
        "membership_id": membership_id,
        "jti": challenge_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.AUTH_MFA_CHALLENGE_MINUTES),
        "type": "mfa_challenge",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_mfa_challenge_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "mfa_challenge" or not payload.get("sub"):
            raise TokenError("Invalid MFA challenge.")
        return payload
    except InvalidTokenError as exc:
        raise TokenError("Invalid or expired MFA challenge.") from exc
