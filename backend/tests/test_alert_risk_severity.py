import pytest

from app.models.alert import AlertSeverity
from app.services.alert_service import AlertService


@pytest.mark.parametrize(
    (
        "detection",
        "risk_level",
        "expected",
    ),
    [
        (
            AlertSeverity.LOW,
            "low",
            AlertSeverity.LOW,
        ),
        (
            AlertSeverity.MEDIUM,
            "medium",
            AlertSeverity.MEDIUM,
        ),
        (
            AlertSeverity.MEDIUM,
            "high",
            AlertSeverity.HIGH,
        ),
        (
            AlertSeverity.MEDIUM,
            "critical",
            AlertSeverity.CRITICAL,
        ),
        (
            AlertSeverity.HIGH,
            "high",
            AlertSeverity.CRITICAL,
        ),
        (
            AlertSeverity.HIGH,
            "critical",
            AlertSeverity.CRITICAL,
        ),
        (
            AlertSeverity.CRITICAL,
            "critical",
            AlertSeverity.CRITICAL,
        ),
        (
            AlertSeverity.CRITICAL,
            "low",
            AlertSeverity.CRITICAL,
        ),
    ],
)
def test_risk_aware_severity(
    detection,
    risk_level,
    expected,
):
    result = (
        AlertService.calculate_effective_severity(
            detection,
            risk_level,
        )
    )

    assert result == expected


def test_unknown_risk_does_not_escalate():
    result = (
        AlertService.calculate_effective_severity(
            AlertSeverity.MEDIUM,
            "unknown",
        )
    )

    assert result == AlertSeverity.MEDIUM


def test_missing_risk_does_not_escalate():
    result = (
        AlertService.calculate_effective_severity(
            AlertSeverity.HIGH,
            None,
        )
    )

    assert result == AlertSeverity.HIGH
