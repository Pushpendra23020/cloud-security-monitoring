from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cloud Security Monitoring"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

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

    # Alert notification configuration
    ALERT_CONSOLE_NOTIFICATIONS: bool = True

    ALERT_WEBHOOK_ENABLED: bool = False
    ALERT_WEBHOOK_URL: str | None = None
    ALERT_WEBHOOK_TIMEOUT: float = 5.0
    ALERT_WEBHOOK_MAX_ATTEMPTS: int = 3
    ALERT_WEBHOOK_BACKOFF_SECONDS: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
