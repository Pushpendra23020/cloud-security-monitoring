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
        "ALERT_WEBHOOK_ORGANIZATION_ID": 1,
        "ALERT_WEBHOOK_TIMEOUT": 5.0,
    }

    values.update(overrides)

    return Settings(**values)


def test_no_channels_enabled():
    settings = build_settings()

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings,
            organization_id=1,
        )
    )

    assert dispatcher.notifiers == []


def test_console_channel_enabled():
    settings = build_settings(
        ALERT_CONSOLE_NOTIFICATIONS=True
    )

    dispatcher = (
        NotificationDispatcherFactory.build(
            settings,
            organization_id=1,
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
            settings,
            organization_id=1,
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
            settings,
            organization_id=1,
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
            settings,
            organization_id=1,
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
            settings,
            organization_id=1,
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
            settings,
            organization_id=1,
        )
    )

    notifier = dispatcher.notifiers[0]

    assert notifier.max_attempts == 5
    assert notifier.backoff_seconds == 2.5


def test_webhook_is_only_enabled_for_its_bound_organization():
    settings = build_settings(
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL="https://example.com/webhook",
        ALERT_WEBHOOK_ORGANIZATION_ID=11,
    )

    matching = NotificationDispatcherFactory.build(settings, organization_id=11)
    other = NotificationDispatcherFactory.build(settings, organization_id=22)

    assert len(matching.notifiers) == 1
    assert isinstance(matching.notifiers[0], WebhookNotifier)
    assert other.notifiers == []


def test_webhook_requires_an_organization_binding():
    settings = build_settings(
        ALERT_WEBHOOK_ENABLED=True,
        ALERT_WEBHOOK_URL="https://example.com/webhook",
        ALERT_WEBHOOK_ORGANIZATION_ID=None,
    )

    with pytest.raises(ValueError, match="ALERT_WEBHOOK_ORGANIZATION_ID"):
        NotificationDispatcherFactory.build(settings, organization_id=1)
