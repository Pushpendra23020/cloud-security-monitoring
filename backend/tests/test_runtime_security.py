import pytest
from types import SimpleNamespace
from sqlalchemy import delete
from uuid import uuid4

from app.config import settings
from app.database.models.organization import OrganizationMembership
from app.database.models.user import User
from app.database.session import SessionLocal
from app.main import bootstrap_phase_10_admin, validate_runtime_security
from app.core.runtime_security import validate_worker_runtime_security
from app.utils.client_ip import resolve_client_ip


def test_production_requires_authentication(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 32)

    with pytest.raises(RuntimeError, match="AUTH_ENABLED"):
        validate_runtime_security()


def test_production_rejects_debug_mode(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 32)

    with pytest.raises(RuntimeError, match="DEBUG"):
        validate_runtime_security()


def test_production_requires_strong_secret(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_runtime_security()


def test_secure_production_configuration_passes(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 32)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "AUTH_MFA_ENCRYPTION_KEY", "mfa-key")

    validate_runtime_security()


def test_production_rejects_incomplete_oidc_configuration(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 32)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "AUTH_MFA_ENCRYPTION_KEY", "mfa-key")
    monkeypatch.setattr(settings, "OIDC_ENABLED", True)
    monkeypatch.setattr(settings, "OIDC_ISSUER_URL", "https://idp.example")
    monkeypatch.setattr(settings, "OIDC_CLIENT_ID", "client")
    monkeypatch.setattr(settings, "OIDC_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "OIDC_REDIRECT_URI", None)

    with pytest.raises(RuntimeError, match="OIDC issuer"):
        validate_runtime_security()


def test_production_requires_secure_cookie_and_independent_mfa_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 32)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)

    with pytest.raises(RuntimeError, match="AUTH_COOKIE_SECURE"):
        validate_runtime_security()

    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "AUTH_MFA_ENCRYPTION_KEY", None)
    with pytest.raises(RuntimeError, match="AUTH_MFA_ENCRYPTION_KEY"):
        validate_runtime_security()


def test_worker_requires_encrypted_s3_archive_in_production(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "EVENT_ARCHIVE_PROVIDER", "filesystem")
    with pytest.raises(RuntimeError, match="EVENT_ARCHIVE_PROVIDER"):
        validate_worker_runtime_security()

    monkeypatch.setattr(settings, "EVENT_ARCHIVE_PROVIDER", "s3")
    monkeypatch.setattr(settings, "EVENT_ARCHIVE_S3_BUCKET", "archive-bucket")
    monkeypatch.setattr(settings, "EVENT_ARCHIVE_S3_KMS_KEY_ID", None)
    with pytest.raises(RuntimeError, match="EVENT_ARCHIVE_S3_KMS_KEY_ID"):
        validate_worker_runtime_security()

    monkeypatch.setattr(settings, "EVENT_ARCHIVE_S3_KMS_KEY_ID", "kms-key")
    monkeypatch.setattr(settings, "EVENT_ARCHIVE_RETENTION_DAYS", 365)
    validate_worker_runtime_security()


def test_forwarded_client_ip_is_used_only_for_trusted_proxy(monkeypatch):
    monkeypatch.setattr(
        settings,
        "AUTH_TRUSTED_PROXY_CIDRS",
        "172.16.0.0/12,127.0.0.0/8",
    )
    trusted_request = SimpleNamespace(
        client=SimpleNamespace(host="172.19.0.6"),
        headers={"X-Forwarded-For": "203.0.113.25, 172.19.0.6"},
    )
    untrusted_request = SimpleNamespace(
        client=SimpleNamespace(host="198.51.100.10"),
        headers={"X-Forwarded-For": "203.0.113.25"},
    )

    assert resolve_client_ip(trusted_request) == "203.0.113.25"
    assert resolve_client_ip(untrusted_request) == "198.51.100.10"


def test_bootstrap_never_resets_an_existing_administrator(monkeypatch):
    suffix = uuid4().hex[:12]
    username = f"bootstrap-{suffix}"
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_BOOTSTRAP_ADMIN_USERNAME", username)
    monkeypatch.setattr(
        settings,
        "AUTH_BOOTSTRAP_ADMIN_EMAIL",
        f"{username}@example.com",
    )
    monkeypatch.setattr(
        settings,
        "AUTH_BOOTSTRAP_ADMIN_PASSWORD",
        f"Initial-bootstrap-{suffix}",
    )

    try:
        bootstrap_phase_10_admin()
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).one()
            original_password_hash = user.password_hash
            membership = (
                db.query(OrganizationMembership)
                .filter(OrganizationMembership.user_id == user.id)
                .one()
            )
            user.email = f"changed-{suffix}@example.com"
            user.role = "viewer"
            user.is_active = False
            membership.role = "viewer"
            membership.is_active = False
            user_id = user.id
            db.commit()

        monkeypatch.setattr(
            settings,
            "AUTH_BOOTSTRAP_ADMIN_PASSWORD",
            f"Different-bootstrap-{suffix}",
        )
        bootstrap_phase_10_admin()

        with SessionLocal() as db:
            user = db.get(User, user_id)
            membership = (
                db.query(OrganizationMembership)
                .filter(OrganizationMembership.user_id == user_id)
                .one()
            )
            assert user.password_hash == original_password_hash
            assert user.email == f"changed-{suffix}@example.com"
            assert user.role == "viewer"
            assert user.is_active is False
            assert membership.role == "viewer"
            assert membership.is_active is False
    finally:
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).one_or_none()
            if user is not None:
                db.execute(
                    delete(OrganizationMembership).where(
                        OrganizationMembership.user_id == user.id
                    )
                )
                db.delete(user)
                db.commit()
