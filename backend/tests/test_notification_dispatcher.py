from datetime import (
    datetime,
    timedelta,
    timezone,
)

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


class SuccessNotifier(AlertNotifier):

    def send(
        self,
        alert: Alert,
    ) -> bool:
        return True


class FailedNotifier(AlertNotifier):

    def send(
        self,
        alert: Alert,
    ) -> bool:
        return False


class ExplodingNotifier(AlertNotifier):

    def send(
        self,
        alert: Alert,
    ) -> bool:
        raise RuntimeError(
            "notification failure"
        )


def build_alert():
    return Alert(
        rule_id="AWS-DISPATCH-001",
        rule_name="Dispatcher Test",
        severity=AlertSeverity.HIGH,
        event_id="event-dispatch-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
    )


def test_successful_dispatch():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    dispatcher = NotificationDispatcher(
        [
            SuccessNotifier(),
        ]
    )

    result = dispatcher.dispatch(
        alert,
        now=now,
    )

    assert result is True

    assert (
        alert.notification_status
        == NotificationStatus.SENT
    )

    assert alert.last_notified_at == now


def test_all_channels_fail():
    alert = build_alert()

    dispatcher = NotificationDispatcher(
        [
            FailedNotifier(),
            ExplodingNotifier(),
        ]
    )

    result = dispatcher.dispatch(
        alert
    )

    assert result is False

    assert (
        alert.notification_status
        == NotificationStatus.FAILED
    )


def test_one_success_is_enough():
    alert = build_alert()

    dispatcher = NotificationDispatcher(
        [
            FailedNotifier(),
            SuccessNotifier(),
        ]
    )

    result = dispatcher.dispatch(
        alert
    )

    assert result is True

    assert (
        alert.notification_status
        == NotificationStatus.SENT
    )


def test_suppressed_alert_not_dispatched():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    alert.suppressed_until = (
        now + timedelta(minutes=30)
    )

    dispatcher = NotificationDispatcher(
        [
            SuccessNotifier(),
        ]
    )

    result = dispatcher.dispatch(
        alert,
        now=now,
    )

    assert result is False

    assert (
        alert.notification_status
        == NotificationStatus.SUPPRESSED
    )


def test_throttled_alert_not_dispatched():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    alert.last_notified_at = (
        now - timedelta(minutes=1)
    )

    dispatcher = NotificationDispatcher(
        [
            SuccessNotifier(),
        ]
    )

    result = dispatcher.dispatch(
        alert,
        now=now,
    )

    assert result is False

    assert (
        alert.notification_status
        == NotificationStatus.SUPPRESSED
    )


def test_no_notifiers_marks_failed():
    alert = build_alert()

    dispatcher = (
        NotificationDispatcher()
    )

    result = dispatcher.dispatch(
        alert
    )

    assert result is False

    assert (
        alert.notification_status
        == NotificationStatus.FAILED
    )
