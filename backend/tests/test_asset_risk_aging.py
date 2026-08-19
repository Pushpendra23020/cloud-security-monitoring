from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.services.asset_risk_service import (
    AssetRiskService,
)


NOW = datetime(
    2026,
    8,
    19,
    8,
    0,
    tzinfo=timezone.utc,
)


def test_fresh_alert_has_full_weight():
    created_at = (
        NOW
        - timedelta(hours=2)
    )

    multiplier = (
        AssetRiskService
        .calculate_age_multiplier(
            created_at,
            now=NOW,
        )
    )

    assert multiplier == 1.0


def test_three_day_alert_has_85_percent_weight():
    created_at = (
        NOW
        - timedelta(days=3)
    )

    multiplier = (
        AssetRiskService
        .calculate_age_multiplier(
            created_at,
            now=NOW,
        )
    )

    assert multiplier == 0.85


def test_two_week_alert_has_60_percent_weight():
    created_at = (
        NOW
        - timedelta(days=14)
    )

    multiplier = (
        AssetRiskService
        .calculate_age_multiplier(
            created_at,
            now=NOW,
        )
    )

    assert multiplier == 0.60


def test_old_alert_has_35_percent_weight():
    created_at = (
        NOW
        - timedelta(days=45)
    )

    multiplier = (
        AssetRiskService
        .calculate_age_multiplier(
            created_at,
            now=NOW,
        )
    )

    assert multiplier == 0.35


def test_three_day_high_alert_contribution():
    created_at = (
        NOW
        - timedelta(days=3)
    )

    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="high",
            status="open",
            created_at=created_at,
            now=NOW,
        )
    )

    assert score == pytest.approx(
        17.0
    )


def test_old_critical_alert_is_decayed():
    created_at = (
        NOW
        - timedelta(days=45)
    )

    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="critical",
            status="open",
            created_at=created_at,
            now=NOW,
        )
    )

    assert score == pytest.approx(
        12.25
    )


def test_resolved_alert_remains_zero():
    created_at = (
        NOW
        - timedelta(hours=1)
    )

    score = (
        AssetRiskService
        .calculate_alert_contribution(
            severity="critical",
            status="resolved",
            created_at=created_at,
            now=NOW,
        )
    )

    assert score == 0
