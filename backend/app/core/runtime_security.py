"""Fail-fast validation for production runtime configuration."""

from app.config import settings


def validate_api_runtime_security() -> None:
    """Reject production configurations that would weaken the public API."""
    if settings.ENVIRONMENT.lower() != "production":
        return
    if not settings.AUTH_ENABLED:
        raise RuntimeError("AUTH_ENABLED must be true in production.")
    if settings.DEBUG:
        raise RuntimeError("DEBUG must be false in production.")
    if len(settings.SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must contain at least 32 characters in production.")
    if not settings.AUTH_COOKIE_SECURE:
        raise RuntimeError("AUTH_COOKIE_SECURE must be true in production.")
    if not settings.AUTH_MFA_ENCRYPTION_KEY:
        raise RuntimeError(
            "AUTH_MFA_ENCRYPTION_KEY must be set independently in production."
        )
    if settings.OIDC_ENABLED and not all(
        (
            settings.OIDC_ISSUER_URL,
            settings.OIDC_CLIENT_ID,
            settings.OIDC_CLIENT_SECRET,
            settings.OIDC_REDIRECT_URI,
        )
    ):
        raise RuntimeError(
            "OIDC issuer, client ID, client secret, and redirect URI are required "
            "when OIDC is enabled in production."
        )


def validate_worker_runtime_security() -> None:
    """Require immutable encrypted archival storage for production workers."""
    if settings.ENVIRONMENT.lower() != "production":
        return
    if settings.EVENT_ARCHIVE_PROVIDER.lower() != "s3":
        raise RuntimeError("EVENT_ARCHIVE_PROVIDER must be s3 in production.")
    if not settings.EVENT_ARCHIVE_S3_BUCKET:
        raise RuntimeError("EVENT_ARCHIVE_S3_BUCKET must be set in production.")
    if not settings.EVENT_ARCHIVE_S3_KMS_KEY_ID:
        raise RuntimeError("EVENT_ARCHIVE_S3_KMS_KEY_ID must be set in production.")
    if settings.EVENT_ARCHIVE_RETENTION_DAYS < 1:
        raise RuntimeError("EVENT_ARCHIVE_RETENTION_DAYS must be at least one day.")
