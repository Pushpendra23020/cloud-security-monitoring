import base64
import hashlib
from uuid import uuid4
from unittest.mock import AsyncMock, patch
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import settings
from app.core.security import decode_access_token, hash_password
from app.database.models.auth_session import AuthSession
from app.database.models.auth_rate_limit import AuthRateLimit
from app.database.models.audit_log import AuditLog
from app.database.models.organization import OrganizationMembership
from app.database.models.user import User
from app.database.session import SessionLocal
from app.main import app
from app.services.mfa_service import MfaService
from app.services.oidc_service import OidcError, OidcService

client = TestClient(app)


def create_user(role: str = "admin") -> tuple[User, str]:
    suffix = uuid4().hex[:10]
    password = f"Phase10-secure-{suffix}"
    with SessionLocal() as db:
        user = User(
            username=f"phase10-{suffix}",
            email=f"phase10-{suffix}@example.com",
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.flush()
        db.add(
            OrganizationMembership(
                organization_id=1,
                user_id=user.id,
                role=role,
            )
        )
        db.commit()
        db.refresh(user)
        db.expunge(user)
    return user, password


def cleanup(*user_ids: int) -> None:
    with SessionLocal() as db:
        usernames = [
            user.username
            for user in db.query(User).filter(User.id.in_(user_ids)).all()
        ]
        if usernames:
            db.execute(delete(AuditLog).where(AuditLog.user.in_(usernames)))
        db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()


def login(user: User, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_status_is_public(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "oidc_enabled": False,
        "oidc_login_url": None,
    }


def test_oidc_start_is_hidden_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "OIDC_ENABLED", False)
    response = client.get("/api/v1/auth/oidc/start", follow_redirects=False)
    assert response.status_code == 404


def test_oidc_start_uses_signed_transaction_cookie(monkeypatch):
    monkeypatch.setattr(settings, "OIDC_ENABLED", True)
    with patch.object(
        OidcService,
        "authorization_url",
        new=AsyncMock(return_value=("https://idp.example/authorize", "signed-transaction")),
    ):
        response = client.get("/api/v1/auth/oidc/start", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://idp.example/authorize"
    cookie = response.headers["set-cookie"]
    assert "cloud_sentinel_oidc=signed-transaction" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_oidc_access_token_hash_is_verified():
    access_token = "test-oidc-access-token"
    digest = hashlib.sha256(access_token.encode()).digest()
    token_hash = base64.urlsafe_b64encode(
        digest[: len(digest) // 2]
    ).rstrip(b"=").decode()

    OidcService._validate_access_token_hash(
        {"at_hash": token_hash},
        "RS256",
        access_token,
    )
    with pytest.raises(OidcError, match="hash validation"):
        OidcService._validate_access_token_hash(
            {"at_hash": "incorrect"},
            "RS256",
            access_token,
        )


def test_oidc_callback_signs_in_preprovisioned_identity(monkeypatch):
    monkeypatch.setattr(settings, "OIDC_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    user, _ = create_user("viewer")
    session_client = TestClient(app)
    try:
        with SessionLocal() as db:
            stored = db.get(User, user.id)
            stored.oidc_issuer = "https://idp.example"
            stored.oidc_subject = "subject-123"
            db.commit()
        session_client.cookies.set(
            settings.OIDC_TRANSACTION_COOKIE_NAME,
            "signed-transaction",
            path="/api/v1/auth/oidc",
        )
        claims = {
            "iss": "https://idp.example",
            "sub": "subject-123",
            "email": user.email,
            "email_verified": True,
        }
        with patch.object(
            OidcService,
            "authenticate_callback",
            new=AsyncMock(return_value=claims),
        ):
            response = session_client.get(
                "/api/v1/auth/oidc/callback?code=authorization-code&state=long-enough-state-value",
                follow_redirects=False,
            )
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert session_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    finally:
        session_client.close()
        cleanup(user.id)


def test_login_and_current_user(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("analyst")
    try:
        token = login(user, password)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == user.username
        assert response.json()["role"] == "analyst"
    finally:
        cleanup(user.id)


def test_login_uses_http_only_revocable_session_cookie(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    user, password = create_user("analyst")
    session_client = TestClient(app)
    try:
        response = session_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        assert response.status_code == 200
        cookie = response.headers["set-cookie"]
        assert "HttpOnly" in cookie
        assert "SameSite=strict" in cookie
        assert "cloud_sentinel_refresh=" in cookie

        payload = decode_access_token(response.json()["access_token"])
        assert payload["sid"]
        with SessionLocal() as db:
            session = db.get(AuthSession, payload["sid"])
            assert session is not None
            assert session.user_id == user.id
    finally:
        session_client.close()
        cleanup(user.id)


def test_refresh_rotation_detects_reuse_and_revokes_session(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    user, password = create_user("analyst")
    session_client = TestClient(app)
    replay_client = TestClient(app)
    try:
        login_response = session_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        old_refresh = session_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        assert old_refresh

        refresh_response = session_client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == 200
        new_refresh = session_client.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        assert new_refresh and new_refresh != old_refresh

        replay_client.cookies.set(
            settings.AUTH_REFRESH_COOKIE_NAME,
            old_refresh,
            path="/api/v1/auth",
        )
        replay_response = replay_client.post("/api/v1/auth/refresh")
        assert replay_response.status_code == 401
        assert replay_response.json()["detail"] == "Session has been revoked."

        assert session_client.post("/api/v1/auth/refresh").status_code == 401
    finally:
        session_client.close()
        replay_client.close()
        cleanup(user.id)


def test_logout_revokes_existing_access_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    user, password = create_user("analyst")
    session_client = TestClient(app)
    try:
        login_response = session_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        token = login_response.json()["access_token"]
        assert session_client.post("/api/v1/auth/logout").status_code == 204
        response = session_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
    finally:
        session_client.close()
        cleanup(user.id)


def test_logout_can_revoke_from_bearer_when_refresh_cookie_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    user, password = create_user("analyst")
    session_client = TestClient(app)
    try:
        login_response = session_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        token = login_response.json()["access_token"]
        session_client.cookies.clear()
        logout_response = session_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == 204
        response = session_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
    finally:
        session_client.close()
        cleanup(user.id)


def test_repeated_failures_lock_account(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_MAX_FAILED_LOGINS", 3)
    monkeypatch.setattr(settings, "AUTH_LOCKOUT_MINUTES", 15)
    user, password = create_user("analyst")
    try:
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": user.username, "password": "Wrong-password-123!"},
            )
            assert response.status_code == 401

        locked_response = client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        assert locked_response.status_code == 401
        assert locked_response.json()["detail"] == "Invalid username or password."
        with SessionLocal() as db:
            locked_user = db.get(User, user.id)
            assert locked_user.failed_login_attempts == 3
            assert locked_user.locked_until is not None
    finally:
        cleanup(user.id)


def test_distributed_rate_limit_blocks_unknown_principal(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_PRINCIPAL_ATTEMPTS", 3)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_IP_ATTEMPTS", 100)
    with SessionLocal() as db:
        db.execute(delete(AuthRateLimit))
        db.commit()
    try:
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "unknown-rate-limit-user",
                    "password": "Wrong-password-123!",
                },
            )
            assert response.status_code == 401
        blocked = client.post(
            "/api/v1/auth/login",
            json={
                "username": "unknown-rate-limit-user",
                "password": "Wrong-password-123!",
            },
        )
        assert blocked.status_code == 429
        assert int(blocked.headers["Retry-After"]) > 0
    finally:
        with SessionLocal() as db:
            db.execute(delete(AuthRateLimit))
            db.commit()


def test_mfa_setup_recovery_login_and_challenge_replay_protection(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)
    user, password = create_user("analyst")
    session_client = TestClient(app)
    try:
        login_response = session_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        setup = session_client.post("/api/v1/auth/mfa/setup", headers=headers)
        assert setup.status_code == 200
        secret = setup.json()["secret"]
        assert secret not in setup.json()["provisioning_uri"].split("secret=", 1)[0]
        code = MfaService._totp(secret, int(time.time()) // 30)
        enabled = session_client.post(
            "/api/v1/auth/mfa/enable",
            headers=headers,
            json={"code": code},
        )
        assert enabled.status_code == 200
        recovery_codes = enabled.json()["recovery_codes"]
        assert len(recovery_codes) == 10

        assert session_client.post("/api/v1/auth/logout", headers=headers).status_code == 204
        password_login = session_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        assert password_login.status_code == 200
        assert password_login.json()["mfa_required"] is True
        assert password_login.json()["access_token"] is None
        challenge = password_login.json()["challenge_token"]

        verified = session_client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_token": challenge, "code": recovery_codes[0]},
        )
        assert verified.status_code == 200
        assert verified.json()["access_token"]

        replay = session_client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_token": challenge, "code": recovery_codes[1]},
        )
        assert replay.status_code == 401
        with SessionLocal() as db:
            refreshed = db.get(User, user.id)
            assert refreshed.mfa_enabled is True
            assert refreshed.mfa_secret_encrypted
            assert secret not in refreshed.mfa_secret_encrypted
    finally:
        session_client.close()
        cleanup(user.id)


def test_login_does_not_recreate_a_removed_membership(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("admin")
    try:
        with SessionLocal() as db:
            db.execute(
                delete(OrganizationMembership).where(
                    OrganizationMembership.user_id == user.id
                )
            )
            db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        assert response.status_code == 401
        with SessionLocal() as db:
            assert (
                db.query(OrganizationMembership)
                .filter(OrganizationMembership.user_id == user.id)
                .count()
                == 0
            )
    finally:
        cleanup(user.id)


def test_protected_api_rejects_missing_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


def test_admin_can_create_user_and_action_is_audited(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    admin, password = create_user("admin")
    created_id = None
    try:
        token = login(admin, password)
        suffix = uuid4().hex[:10]
        response = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": f"analyst-{suffix}",
                "email": f"analyst-{suffix}@example.com",
                "password": f"Analyst-secure-{suffix}",
                "role": "analyst",
            },
        )
        assert response.status_code == 201
        created_id = response.json()["id"]
        with SessionLocal() as db:
            audit = db.query(AuditLog).filter_by(
                user=admin.username,
                action="POST /api/v1/users",
            ).one()
            assert audit.status_code == 201
    finally:
        cleanup(*(value for value in (admin.id, created_id) if value is not None))


def test_non_admin_cannot_manage_users(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("viewer")
    try:
        token = login(user, password)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
    finally:
        cleanup(user.id)


def test_admin_can_link_and_unlink_preprovisioned_oidc_identity(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    admin, password = create_user("admin")
    target, _ = create_user("viewer")
    try:
        token = login(admin, password)
        headers = {"Authorization": f"Bearer {token}"}
        linked = client.put(
            f"/api/v1/users/{target.id}/oidc-identity",
            headers=headers,
            json={
                "issuer": "https://idp.example/",
                "subject": "enterprise-subject-123",
            },
        )
        assert linked.status_code == 200
        assert linked.json() == {
            "user_id": target.id,
            "issuer": "https://idp.example",
            "subject": "enterprise-subject-123",
        }
        listed = client.get("/api/v1/users", headers=headers)
        target_response = next(
            item for item in listed.json() if item["id"] == target.id
        )
        assert target_response["oidc_linked"] is True

        unlinked = client.delete(
            f"/api/v1/users/{target.id}/oidc-identity",
            headers=headers,
        )
        assert unlinked.status_code == 204
        with SessionLocal() as db:
            stored = db.get(User, target.id)
            assert stored.oidc_subject is None
            assert stored.oidc_issuer is None
    finally:
        cleanup(admin.id, target.id)


def test_non_admin_cannot_create_cloud_accounts(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("analyst")
    try:
        token = login(user, password)
        response = client.post(
            "/api/v1/cloud-accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "provider": "aws",
                "account_id": "123456789012",
                "region": "ap-south-1",
            },
        )
        assert response.status_code == 403
    finally:
        cleanup(user.id)


def test_non_admin_cannot_invoke_aws_management(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("analyst")
    try:
        token = login(user, password)
        response = client.get(
            "/api/v1/aws/identity",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
    finally:
        cleanup(user.id)


def test_platform_aws_identity_diagnostic_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "PLATFORM_DIAGNOSTICS_ENABLED", False)
    admin, password = create_user("admin")
    try:
        token = login(admin, password)
        with patch("app.api.v1.aws.AWSService.verify_connection") as verify:
            response = client.get(
                "/api/v1/aws/identity",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 404
        verify.assert_not_called()
    finally:
        cleanup(admin.id)
