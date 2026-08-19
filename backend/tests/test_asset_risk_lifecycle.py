from app.services.asset_risk_service import (
    AssetRiskService,
)


def test_open_high_alert_full_risk():
    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="high",
            status="open",
        )
    )

    assert score == 20


def test_acknowledged_high_alert_reduced():
    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="high",
            status="acknowledged",
        )
    )

    assert score == 18


def test_investigating_critical_full_risk():
    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="critical",
            status="investigating",
        )
    )

    assert score == 35


def test_resolved_alert_zero_risk():
    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="critical",
            status="resolved",
        )
    )

    assert score == 0


def test_false_positive_alert_zero_risk():
    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="critical",
            status="false_positive",
        )
    )

    assert score == 0


def test_resolved_finding_zero_risk():
    score = (
        AssetRiskService
        .calculate_finding_contribution(
            severity="high",
            status="resolved",
        )
    )

    assert score == 0
