from datetime import datetime, timezone

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


def build_alert(
    alert_id: str,
) -> Alert:
    return Alert(
        alert_id=alert_id,
        rule_id="AWS-INTEGRATION-001",
        rule_name="Notification Integration",
        severity=AlertSeverity.HIGH,
        event_id=f"event-{alert_id}",
        event_name="ConsoleLogin",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        source_ip="192.0.2.10",
    )


def test_new_alert_dispatches_notification(
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

    alert = build_alert(
        "alert-001"
    )

    assert service.save_alert(
        alert
    ) is True

    stored = service.get_alert(
        "alert-001"
    )

    assert stored is not None

    assert notifier.calls == 1

    assert (
        stored.notification_status
        == NotificationStatus.SENT
    )

    assert (
        stored.last_notified_at
        is not None
    )


def test_no_dispatcher_keeps_old_behavior(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(
        store
    )

    alert = build_alert(
        "alert-001"
    )

    assert service.save_alert(
        alert
    ) is True

    stored = service.get_alert(
        "alert-001"
    )

    assert stored is not None

    assert (
        stored.notification_status
        == NotificationStatus.PENDING
    )


def test_duplicate_is_throttled(
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

    first = build_alert(
        "alert-001"
    )

    second = build_alert(
        "alert-002"
    )

    assert service.save_alert(
        first
    ) is True

    assert service.save_alert(
        second
    ) is True

    alerts = service.get_all_alerts()

    assert len(alerts) == 1

    stored = alerts[0]

    assert (
        stored.occurrence_count
        == 2
    )

    assert notifier.calls == 1

    assert (
        stored.notification_status
        == NotificationStatus.SUPPRESSED
    )


def test_notification_state_is_persisted(
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

    alert = build_alert(
        "alert-001"
    )

    service.save_alert(
        alert
    )

    reloaded = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    stored = reloaded.get(
        "alert-001"
    )

    assert stored is not None

    assert (
        stored.notification_status
        == NotificationStatus.SENT
    )

    assert (
        stored.last_notified_at
        is not None
    )
