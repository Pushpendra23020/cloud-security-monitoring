from unittest.mock import MagicMock, patch

from app.services.asset_risk_refresh_service import (
    AssetRiskRefreshService,
)


def test_refresh_stale_assets():
    db = MagicMock()

    asset_one = MagicMock()
    asset_one.id = 1
    asset_one.asset_id = "i-one"

    asset_two = MagicMock()
    asset_two.id = 2
    asset_two.asset_id = "i-two"

    with patch(
        "app.services.asset_risk_refresh_service."
        "AssetRepository.get_risk_refresh_batch",
        side_effect=[
            [
                asset_one,
                asset_two,
            ],
            [],
        ],
    ), patch(
        "app.services.asset_risk_refresh_service."
        "AssetRiskService.enrich_asset"
    ) as enrich:
        result = (
            AssetRiskRefreshService
            .refresh_stale(
                db=db,
                batch_size=100,
                stale_minutes=60,
            )
        )

    assert result == {
        "scanned": 2,
        "refreshed": 2,
        "failed": 0,
        "batches": 1,
    }

    assert enrich.call_count == 2

    assert (
        db.commit.call_count
        == 1
    )


def test_refresh_continues_after_asset_failure():
    db = MagicMock()

    asset_one = MagicMock()
    asset_one.id = 1
    asset_one.asset_id = "i-one"

    asset_two = MagicMock()
    asset_two.id = 2
    asset_two.asset_id = "i-two"

    with patch(
        "app.services.asset_risk_refresh_service."
        "AssetRepository.get_risk_refresh_batch",
        side_effect=[
            [
                asset_one,
                asset_two,
            ],
            [],
        ],
    ), patch(
        "app.services.asset_risk_refresh_service."
        "AssetRiskService.enrich_asset",
        side_effect=[
            RuntimeError("boom"),
            asset_two,
        ],
    ):
        result = (
            AssetRiskRefreshService
            .refresh_stale(
                db=db,
                batch_size=100,
                stale_minutes=60,
            )
        )

    assert result == {
        "scanned": 2,
        "refreshed": 1,
        "failed": 1,
        "batches": 1,
    }

    assert (
        db.commit.call_count
        == 1
    )


def test_refresh_stale_uses_keyset_cursor():
    db = MagicMock()

    asset_one = MagicMock()
    asset_one.id = 10
    asset_one.asset_id = "i-ten"

    asset_two = MagicMock()
    asset_two.id = 20
    asset_two.asset_id = "i-twenty"

    with patch(
        "app.services.asset_risk_refresh_service."
        "AssetRepository.get_risk_refresh_batch",
        side_effect=[
            [asset_one],
            [asset_two],
            [],
        ],
    ) as get_batch, patch(
        "app.services.asset_risk_refresh_service."
        "AssetRiskService.enrich_asset"
    ):
        result = (
            AssetRiskRefreshService
            .refresh_stale(
                db=db,
                batch_size=1,
                stale_minutes=60,
            )
        )

    assert result == {
        "scanned": 2,
        "refreshed": 2,
        "failed": 0,
        "batches": 2,
    }

    assert (
        get_batch.call_args_list[0]
        .kwargs["after_id"]
        == 0
    )

    assert (
        get_batch.call_args_list[1]
        .kwargs["after_id"]
        == 10
    )

    assert (
        get_batch.call_args_list[2]
        .kwargs["after_id"]
        == 20
    )


def test_invalid_batch_size_rejected():
    db = MagicMock()

    try:
        AssetRiskRefreshService.refresh_stale(
            db=db,
            batch_size=0,
            stale_minutes=60,
        )

    except ValueError as exc:
        assert (
            "batch_size"
            in str(exc)
        )

    else:
        raise AssertionError(
            "Expected ValueError"
        )
