from datetime import datetime, timedelta, timezone

import pytest

from app.models.alert import (
    Alert,
    AlertSeverity,
    NotificationStatus,
)
from app.services.alert_notification_policy import (
    AlertNotificationPolicy,
)


def build_alert(
    *,
    severity=AlertSeverity.HIGH,
):
    return Alert(
        rule_id="AWS-TEST-001",
        rule_name="Notification Test",
        severity=severity,
        event_id="event-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
    )


def test_new_alert_can_notify():
    alert = build_alert()

    assert (
        AlertNotificationPolicy.should_notify(
            alert
        )
        is True
    )


def test_manual_suppression_blocks_notification():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    alert.suppressed_until = (
        now + timedelta(minutes=30)
    )

    assert (
        AlertNotificationPolicy.should_notify(
            alert,
            now=now,
        )
        is False
    )


def test_expired_suppression_allows_notification():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    alert.suppressed_until = (
        now - timedelta(minutes=1)
    )

    assert (
        AlertNotificationPolicy.should_notify(
            alert,
            now=now,
        )
        is True
    )


def test_high_alert_is_throttled_for_five_minutes():
    now = datetime.now(timezone.utc)

    alert = build_alert(
        severity=AlertSeverity.HIGH
    )

    alert.last_notified_at = (
        now - timedelta(minutes=2)
    )

    assert (
        AlertNotificationPolicy.should_notify(
            alert,
            now=now,
        )
        is False
    )


def test_high_alert_can_notify_after_window():
    now = datetime.now(timezone.utc)

    alert = build_alert(
        severity=AlertSeverity.HIGH
    )

    alert.last_notified_at = (
        now - timedelta(minutes=6)
    )

    assert (
        AlertNotificationPolicy.should_notify(
            alert,
            now=now,
        )
        is True
    )


def test_critical_alert_has_shorter_window():
    now = datetime.now(timezone.utc)

    alert = build_alert(
        severity=AlertSeverity.CRITICAL
    )

    alert.last_notified_at = (
        now - timedelta(minutes=2)
    )

    assert (
        AlertNotificationPolicy.should_notify(
            alert,
            now=now,
        )
        is True
    )


def test_apply_policy_sets_suppressed():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    alert.suppressed_until = (
        now + timedelta(minutes=10)
    )

    allowed = (
        AlertNotificationPolicy.apply_policy(
            alert,
            now=now,
        )
    )

    assert allowed is False
    assert (
        alert.notification_status
        == NotificationStatus.SUPPRESSED
    )


def test_apply_policy_sets_pending():
    alert = build_alert()

    allowed = (
        AlertNotificationPolicy.apply_policy(
            alert
        )
    )

    assert allowed is True
    assert (
        alert.notification_status
        == NotificationStatus.PENDING
    )


def test_mark_sent():
    now = datetime.now(timezone.utc)

    alert = build_alert()

    AlertNotificationPolicy.mark_sent(
        alert,
        now=now,
    )

    assert (
        alert.notification_status
        == NotificationStatus.SENT
    )
    assert alert.last_notified_at == now


def test_mark_failed():
    alert = build_alert()

    AlertNotificationPolicy.mark_failed(
        alert
    )

    assert (
        alert.notification_status
        == NotificationStatus.FAILED
    )


@pytest.mark.parametrize(
    (
        "severity",
        "minutes",
        "expected",
    ),
    [
        (
            AlertSeverity.CRITICAL,
            1,
            True,
        ),
        (
            AlertSeverity.HIGH,
            5,
            True,
        ),
        (
            AlertSeverity.MEDIUM,
            15,
            True,
        ),
        (
            AlertSeverity.LOW,
            30,
            True,
        ),
        (
            AlertSeverity.INFO,
            60,
            True,
        ),
    ],
)
def test_each_severity_throttle_boundary(
    severity,
    minutes,
    expected,
):
    now = datetime.now(timezone.utc)

    alert = build_alert(
        severity=severity
    )

    alert.last_notified_at = (
        now - timedelta(minutes=minutes)
    )

    result = (
        AlertNotificationPolicy.should_notify(
            alert,
            now=now,
        )
    )

    assert result is expected
