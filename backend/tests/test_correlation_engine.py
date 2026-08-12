from datetime import datetime, timedelta, timezone

from app.models.security_event import SecurityEvent
from app.rules.aws_correlation_rules import (
    AWS_CORRELATION_RULES,
)
from app.rules.correlation_engine import (
    CorrelationEngine,
)


BASE_TIME = datetime(
    2026,
    8,
    12,
    10,
    0,
    tzinfo=timezone.utc,
)


def build_failed_login(
    *,
    event_id: str,
    minute: int,
    source_ip: str = "192.0.2.10",
) -> SecurityEvent:
    return SecurityEvent(
        event_id=event_id,
        timestamp=(
            BASE_TIME
            + timedelta(minutes=minute)
        ),
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        source_ip=source_ip,
        success=False,
        raw_event={
            "responseElements": {
                "ConsoleLogin": "Failure",
            },
            "additionalEventData": {
                "MFAUsed": "No",
            },
        },
    )


def test_no_alert_below_threshold():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES
    )

    alerts = []

    for i in range(4):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"event-{i}",
                    minute=i,
                )
            )
        )

    assert alerts == []


def test_alert_when_threshold_reached():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES
    )

    alerts = []

    for i in range(5):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"event-{i}",
                    minute=i,
                )
            )
        )

    assert len(alerts) == 1

    alert = alerts[0]

    assert alert.rule_id == "AWS-CORR-001"
    assert alert.severity == "high"

    assert (
        alert.metadata[
            "matched_event_count"
        ]
        == 5
    )


def test_different_source_ips_do_not_combine():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES
    )

    alerts = []

    for i in range(3):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"a-{i}",
                    minute=i,
                    source_ip="192.0.2.10",
                )
            )
        )

    for i in range(3):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"b-{i}",
                    minute=i,
                    source_ip="198.51.100.20",
                )
            )
        )

    assert alerts == []


def test_events_outside_window_do_not_combine():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES
    )

    minutes = [
        0,
        1,
        2,
        3,
        20,
    ]

    alerts = []

    for i, minute in enumerate(minutes):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"event-{i}",
                    minute=minute,
                )
            )
        )

    assert alerts == []

def test_repeated_events_are_suppressed_during_cooldown():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES,
        cooldown_minutes=10,
    )

    alerts = []

    for i in range(8):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"event-{i}",
                    minute=i,
                )
            )
        )

    correlation_alerts = [
        alert
        for alert in alerts
        if alert.rule_id
        == "AWS-CORR-001"
    ]

    assert len(
        correlation_alerts
    ) == 1

def test_new_alert_after_cooldown_expires():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES,
        cooldown_minutes=10,
    )

    alerts = []

    first_wave = [
        0,
        1,
        2,
        3,
        4,
    ]

    for i, minute in enumerate(
        first_wave
    ):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"first-{i}",
                    minute=minute,
                )
            )
        )

    second_wave = [
        15,
        16,
        17,
        18,
        19,
    ]

    for i, minute in enumerate(
        second_wave
    ):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"second-{i}",
                    minute=minute,
                )
            )
        )

    correlation_alerts = [
        alert
        for alert in alerts
        if alert.rule_id
        == "AWS-CORR-001"
    ]

    assert len(
        correlation_alerts
    ) == 2

def test_cooldown_is_separate_per_source_ip():
    engine = CorrelationEngine(
        AWS_CORRELATION_RULES,
        cooldown_minutes=10,
    )

    alerts = []

    for i in range(5):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"a-{i}",
                    minute=i,
                    source_ip="192.0.2.10",
                )
            )
        )

    for i in range(5):
        alerts.extend(
            engine.process(
                build_failed_login(
                    event_id=f"b-{i}",
                    minute=i,
                    source_ip="198.51.100.20",
                )
            )
        )

    correlation_alerts = [
        alert
        for alert in alerts
        if alert.rule_id
        == "AWS-CORR-001"
    ]

    assert len(
        correlation_alerts
    ) == 2
