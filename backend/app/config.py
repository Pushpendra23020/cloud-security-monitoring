from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cloud Security Monitoring"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Runtime / observability configuration
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Legacy/direct database URL.
    # Useful for local development, tests, and CI.
    DATABASE_URL: str | None = None

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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Phase 10 identity and access management. Authentication remains
    # opt-in for local/test compatibility and is enabled in production via
    # AUTH_ENABLED=true.
    AUTH_ENABLED: bool = False
    AUTH_BOOTSTRAP_ADMIN_USERNAME: str | None = None
    AUTH_BOOTSTRAP_ADMIN_EMAIL: str | None = None
    AUTH_BOOTSTRAP_ADMIN_PASSWORD: str | None = None

    # Alert notification configuration
    ALERT_CONSOLE_NOTIFICATIONS: bool = True

    ALERT_WEBHOOK_ENABLED: bool = False
    ALERT_WEBHOOK_URL: str | None = None
    ALERT_WEBHOOK_TIMEOUT: float = 5.0
    ALERT_WEBHOOK_MAX_ATTEMPTS: int = 3
    ALERT_WEBHOOK_BACKOFF_SECONDS: float = 1.0
    EVENT_INGEST_API_KEY: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
