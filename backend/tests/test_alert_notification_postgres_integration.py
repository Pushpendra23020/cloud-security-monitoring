from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from app.database.session import SessionLocal
from app.models.alert import (
    Alert,
    AlertSeverity,
    NotificationStatus,
)
from app.notifications.base import AlertNotifier
from app.notifications.dispatcher import (
    NotificationDispatcher,
)
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from app.services.alert_service import AlertService


class RecordingNotifier(AlertNotifier):
    def __init__(self):
        self.calls = 0

    def send(
        self,
        alert: Alert,
    ) -> bool:
        self.calls += 1
        return True


def build_alert() -> Alert:
    suffix = str(uuid4())

    return Alert(
        alert_id=f"alert-{suffix}",
        rule_id="AWS-NOTIFY-POSTGRES-001",
        rule_name="PostgreSQL Notification Test",
        severity=AlertSeverity.HIGH,
        event_id=f"event-{suffix}",
        event_name="ConsoleLogin",
        detection_key=f"detection-{suffix}",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        source_ip="192.0.2.10",
        user_identity=f"test-user-{suffix}",
    )


def test_postgres_suppression_persists():
    alert = build_alert()

    with SessionLocal() as session:
        repository = PostgresAlertRepository(
            session
        )

        service = AlertService(
            repository
        )

        assert service.save_alert(
            alert
        ) is True

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

        stored = repository.get(
            alert.alert_id
        )

        assert stored is not None

        assert (
            stored.notification_status
            == NotificationStatus.SUPPRESSED
        )

        assert stored.suppressed_until is not None



def test_postgres_unsuppression_persists():
    alert = build_alert()

    with SessionLocal() as session:
        repository = PostgresAlertRepository(
            session
        )

        service = AlertService(
            repository
        )

        assert service.save_alert(
            alert
        ) is True

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

        stored = repository.get(
            alert.alert_id
        )

        assert stored is not None
        assert stored.suppressed_until is None

        assert (
            stored.notification_status
            == NotificationStatus.PENDING
        )


def test_postgres_manual_retry_persists():
    alert = build_alert()

    notifier = RecordingNotifier()

    dispatcher = NotificationDispatcher(
        [notifier]
    )

    with SessionLocal() as session:
        repository = PostgresAlertRepository(
            session
        )

        service = AlertService(
            repository=repository,
            dispatcher=dispatcher,
        )

        assert service.save_alert(
            alert
        ) is True

        assert notifier.calls == 1

        result = service.retry_notification(
            alert.alert_id
        )

        assert result is not None
        assert notifier.calls == 2

        stored = repository.get(
            alert.alert_id
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
