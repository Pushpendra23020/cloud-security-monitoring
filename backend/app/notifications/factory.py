from app.config import Settings
from app.notifications.console import (
    ConsoleNotifier,
)
from app.notifications.dispatcher import (
    NotificationDispatcher,
)
from app.notifications.webhook import (
    WebhookNotifier,
)


class NotificationDispatcherFactory:

    @staticmethod
    def build(
        settings: Settings,
        organization_id: int | None = None,
    ) -> NotificationDispatcher:
        notifiers = []

        if (
            settings.ALERT_CONSOLE_NOTIFICATIONS
        ):
            notifiers.append(
                ConsoleNotifier()
            )

        if settings.ALERT_WEBHOOK_ENABLED:
            if not settings.ALERT_WEBHOOK_URL:
                raise ValueError(
                    "ALERT_WEBHOOK_URL is required "
                    "when ALERT_WEBHOOK_ENABLED=true"
                )
            if settings.ALERT_WEBHOOK_ORGANIZATION_ID is None:
                raise ValueError(
                    "ALERT_WEBHOOK_ORGANIZATION_ID is required "
                    "when ALERT_WEBHOOK_ENABLED=true"
                )

            if organization_id == settings.ALERT_WEBHOOK_ORGANIZATION_ID:
                notifiers.append(
                    WebhookNotifier(
                        settings.ALERT_WEBHOOK_URL,
                        timeout=(
                            settings.ALERT_WEBHOOK_TIMEOUT
                        ),
                        max_attempts=(
                            settings.ALERT_WEBHOOK_MAX_ATTEMPTS
                        ),
                        backoff_seconds=(
                            settings.ALERT_WEBHOOK_BACKOFF_SECONDS
                        ),
                    )
                )

        return NotificationDispatcher(
            notifiers
        )
