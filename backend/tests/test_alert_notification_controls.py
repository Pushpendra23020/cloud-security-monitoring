from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.models.alert import (
    Alert,
    AlertSeverity,
    NotificationStatus,
)
from app.notifications.base import (
    AlertNotifier,
)
from app.notifications.dispatcher import (
    NotificationDispatcher,
)
from app.services.alert_service import (
    AlertService,
)
from app.storage.json_alert_store import (
    JsonAlertStore,
)


class RecordingNotifier(AlertNotifier):
    def __init__(self):
        self.calls = 0

    def send(
        self,
        alert: Alert,
    ) -> bool:
        self.calls += 1
        return True


def build_alert():
    return Alert(
        alert_id="alert-control-001",
        rule_id="AWS-CONTROL-001",
        rule_name="Notification Control Test",
        severity=AlertSeverity.HIGH,
        event_id="event-control-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
    )


def build_service(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    notifier = RecordingNotifier()

    dispatcher = NotificationDispatcher(
        [notifier]
    )

    service = AlertService(
        store,
        dispatcher,
    )

    return service, notifier


def test_suppress_alert(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    alert = build_alert()

    service.save_alert(alert)

    until = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    result = (
        service.suppress_alert_notifications(
            alert.alert_id,
            until,
        )
    )

    assert result is not None

    assert (
        result.notification_status
        == NotificationStatus.SUPPRESSED
    )

    assert (
        result.suppressed_until
        == until
    )


def test_suppress_requires_future_time(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    alert = build_alert()

    service.save_alert(alert)

    past = (
        datetime.now(timezone.utc)
        - timedelta(minutes=1)
    )

    with pytest.raises(ValueError):
        service.suppress_alert_notifications(
            alert.alert_id,
            past,
        )


def test_unsuppress_alert(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    alert = build_alert()

    service.save_alert(alert)

    until = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    service.suppress_alert_notifications(
        alert.alert_id,
        until,
    )

    result = (
        service.unsuppress_alert_notifications(
            alert.alert_id
        )
    )

    assert result is not None

    assert result.suppressed_until is None

    assert (
        result.notification_status
        == NotificationStatus.PENDING
    )


def test_manual_retry_dispatches(
    tmp_path,
):
    service, notifier = build_service(
        tmp_path
    )

    alert = build_alert()

    service.save_alert(alert)

    assert notifier.calls == 1

    result = (
        service.retry_notification(
            alert.alert_id
        )
    )

    assert result is not None

    assert notifier.calls == 2

    assert (
        result.notification_status
        == NotificationStatus.SENT
    )


def test_manual_retry_respects_explicit_suppression(
    tmp_path,
):
    service, notifier = build_service(
        tmp_path
    )

    alert = build_alert()

    service.save_alert(alert)

    until = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    service.suppress_alert_notifications(
        alert.alert_id,
        until,
    )

    result = (
        service.retry_notification(
            alert.alert_id
        )
    )

    assert result is not None
    assert notifier.calls == 1

    assert (
        result.notification_status
        == NotificationStatus.SUPPRESSED
    )


def test_missing_alert_returns_none(
    tmp_path,
):
    service, _ = build_service(
        tmp_path
    )

    assert (
        service.retry_notification(
            "missing-alert"
        )
        is None
    )
