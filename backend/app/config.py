from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cloud Security Monitoring"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str

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

