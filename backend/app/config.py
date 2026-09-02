from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cloud Security Monitoring"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Runtime / observability configuration
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    METRICS_ENABLED: bool = False
    PLATFORM_DIAGNOSTICS_ENABLED: bool = False

    # Legacy/direct database URL.
    # Useful for local development, tests, and CI.
    DATABASE_URL: str | None = None
    MIGRATION_DATABASE_URL: str | None = None

    # Optional PostgreSQL role assumed by application connections after login.
    # The migration connection remains privileged and never assumes this role.
    DATABASE_RUNTIME_ROLE: str | None = None
    RLS_ENFORCEMENT_REQUIRED: bool = False

    # Structured PostgreSQL configuration.
    # Used by Docker/Compose and safely supports reserved
    # characters in passwords.
    POSTGRES_DB: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    AWS_REGION: str = "ap-south-1"
    AWS_PROFILE: str | None = None

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10

    # Phase 10 identity and access management. Authentication remains
    # secure by default. Tests or explicitly isolated local environments may
    # opt out with AUTH_ENABLED=false.
    AUTH_ENABLED: bool = True
    AUTH_BOOTSTRAP_ADMIN_USERNAME: str | None = None
    AUTH_BOOTSTRAP_ADMIN_EMAIL: str | None = None
    AUTH_BOOTSTRAP_ADMIN_PASSWORD: str | None = None
    AUTH_SESSION_EXPIRE_DAYS: int = 7
    AUTH_MAX_FAILED_LOGINS: int = 5
    AUTH_LOCKOUT_MINUTES: int = 15
    AUTH_REFRESH_COOKIE_NAME: str = "cloud_sentinel_refresh"
    AUTH_COOKIE_SECURE: bool | None = None
    AUTH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "strict"
    AUTH_MFA_ENCRYPTION_KEY: str | None = None
    AUTH_MFA_ISSUER: str = "Cloud Sentinel"
    AUTH_MFA_CHALLENGE_MINUTES: int = 5
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 300
    AUTH_RATE_LIMIT_BLOCK_SECONDS: int = 900
    AUTH_RATE_LIMIT_PRINCIPAL_ATTEMPTS: int = 10
    AUTH_RATE_LIMIT_IP_ATTEMPTS: int = 50
    AUTH_TRUSTED_PROXY_CIDRS: str = ""

    OIDC_ENABLED: bool = False
    OIDC_ISSUER_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_CLIENT_SECRET: str | None = None
    OIDC_REDIRECT_URI: str | None = None
    OIDC_SCOPES: str = "openid email profile"
    OIDC_ALLOWED_ALGORITHMS: str = "RS256"
    OIDC_ALLOW_EMAIL_LINKING: bool = False
    OIDC_ALLOWED_EMAIL_DOMAINS: str = ""
    OIDC_TRANSACTION_COOKIE_NAME: str = "cloud_sentinel_oidc"

    # Alert notification configuration
    ALERT_CONSOLE_NOTIFICATIONS: bool = True

    ALERT_WEBHOOK_ENABLED: bool = False
    ALERT_WEBHOOK_URL: str | None = None
    ALERT_WEBHOOK_ORGANIZATION_ID: int | None = None
    ALERT_WEBHOOK_TIMEOUT: float = 5.0
    ALERT_WEBHOOK_MAX_ATTEMPTS: int = 3
    ALERT_WEBHOOK_BACKOFF_SECONDS: float = 1.0
    EVENT_INGEST_API_KEY: str | None = None
    EVENT_QUEUE_BATCH_SIZE: int = 25
    EVENT_QUEUE_POLL_SECONDS: float = 2.0
    EVENT_QUEUE_MAX_ATTEMPTS: int = 5
    EVENT_QUEUE_LOCK_TIMEOUT_SECONDS: int = 300
    EVENT_QUEUE_RETRY_BASE_SECONDS: int = 10
    EVENT_QUEUE_ALERT_AGE_SECONDS: int = 300
    EVENT_DATABASE_RETENTION_DAYS: int = 30
    EVENT_RETENTION_CLEANUP_INTERVAL_SECONDS: int = 3600
    EVENT_RETENTION_CLEANUP_BATCH_SIZE: int = 500

    EVENT_ARCHIVE_PROVIDER: str = "filesystem"
    EVENT_ARCHIVE_PATH: str = "/var/lib/cloud-security/archive"
    EVENT_ARCHIVE_S3_BUCKET: str | None = None
    EVENT_ARCHIVE_S3_PREFIX: str = "security-events"
    EVENT_ARCHIVE_S3_KMS_KEY_ID: str | None = None
    EVENT_ARCHIVE_RETENTION_DAYS: int = 365
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
