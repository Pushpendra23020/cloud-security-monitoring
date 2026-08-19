import pytest

from app.config import Settings
from app.notifications.console import (
    ConsoleNotifier,
)
from app.notifications.factory import (
    NotificationDispatcherFactory,
)
from app.notifications.webhook import (
    WebhookNotifier,
)


def build_settings(
    **overrides,
):
    values = {
        "DATABASE_URL": (
            "postgresql://test:test@localhost/test"
        ),
        "SECRET_KEY": "test-secret",
        "ALERT_CONSOLE_NOTIFICATIONS": False,
        "ALERT_WEBHOOK_ENABLED": False,
        "ALERT_WEBHOOK_URL": None,
        "ALERT_WEBHOOK_TIMEOUT": 5.0,
    }

    values.update(overrides)

    return Settings(**values)


def test_no_channels_enabled():
    settings = build_settings()

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings
        )
    )

    assert dispatcher.notifiers == []


def test_console_channel_enabled():
    settings = build_settings(
        ALERT_CONSOLE_NOTIFICATIONS=True
    )

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings
        )
    )

    assert len(
        dispatcher.notifiers
    ) == 1

    assert isinstance(
        dispatcher.notifiers[0],
        ConsoleNotifier,
    )


def test_webhook_channel_enabled():
    settings = build_settings(
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL=(
            "https://example.com/webhook"
        ),
    )

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings
        )
    )

    assert len(
        dispatcher.notifiers
    ) == 1

    notifier = dispatcher.notifiers[0]

    assert isinstance(
        notifier,
        WebhookNotifier,
    )

    assert (
        notifier.url
        == "https://example.com/webhook"
    )


def test_console_and_webhook_enabled():
    settings = build_settings(
        ALERT_CONSOLE_NOTIFICATIONS=True,
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL=(
            "https://example.com/webhook"
        ),
    )

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings
        )
    )

    assert len(
        dispatcher.notifiers
    ) == 2

    assert isinstance(
        dispatcher.notifiers[0],
        ConsoleNotifier,
    )

    assert isinstance(
        dispatcher.notifiers[1],
        WebhookNotifier,
    )


def test_webhook_requires_url():
    settings = build_settings(
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL=None,
    )

    with pytest.raises(
        ValueError,
        match="ALERT_WEBHOOK_URL",
    ):
        NotificationDispatcherFactory.build(
            settings
        )


def test_webhook_timeout_configured():
    settings = build_settings(
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL=(
            "https://example.com/webhook"
        ),
        ALERT_WEBHOOK_TIMEOUT=12.5,
    )

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings
        )
    )

    notifier = dispatcher.notifiers[0]

    assert (
        notifier.timeout
        == 12.5
    )


def test_webhook_retry_settings_configured():
    settings = build_settings(
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL=(
            "https://example.com/webhook"
        ),
        ALERT_WEBHOOK_MAX_ATTEMPTS=5,
        ALERT_WEBHOOK_BACKOFF_SECONDS=2.5,
    )

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings
        )
    )

    notifier = dispatcher.notifiers[0]

    assert notifier.max_attempts == 5
    assert notifier.backoff_seconds == 2.5
