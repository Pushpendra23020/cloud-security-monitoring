import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.repositories.asset_repository import (
    AssetRepository,
)
from app.services.asset_risk_service import (
    AssetRiskService,
)


logger = logging.getLogger(__name__)


class AssetRiskRefreshService:

    DEFAULT_BATCH_SIZE = 100
    DEFAULT_STALE_MINUTES = 60

    @classmethod
    def refresh_stale(
        cls,
        db: Session,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        stale_minutes: int = DEFAULT_STALE_MINUTES,
    ) -> dict[str, int]:
        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0"
            )

        if stale_minutes < 0:
            raise ValueError(
                "stale_minutes cannot be negative"
            )

        stale_before = (
            datetime.now(timezone.utc)
            - timedelta(
                minutes=stale_minutes
            )
        )

        scanned = 0
        refreshed = 0
        failed = 0
        batches = 0
        after_id = 0

        while True:
            assets = (
                AssetRepository
                .get_risk_refresh_batch(
                    db=db,
                    stale_before=stale_before,
                    batch_size=batch_size,
                    after_id=after_id,
                )
            )

            if not assets:
                break

            batches += 1

            for asset in assets:
                scanned += 1

                #
                # Advance cursor regardless of
                # individual asset success.
                #
                after_id = max(
                    after_id,
                    asset.id,
                )

                try:
                    #
                    # Savepoint isolates a single
                    # asset failure without destroying
                    # the whole batch transaction.
                    #
                    with db.begin_nested():
                        AssetRiskService.enrich_asset(
                            db=db,
                            asset=asset,
                            commit=False,
                        )

                    refreshed += 1

                except Exception:
                    failed += 1

                    logger.exception(
                        (
                            "asset_risk_refresh_failed "
                            "asset_id=%s"
                        ),
                        asset.asset_id,
                    )

            #
            # Commit once per bounded batch.
            #
            db.commit()

            logger.info(
                (
                    "asset_risk_batch_complete "
                    "batch=%s "
                    "batch_size=%s "
                    "scanned=%s "
                    "refreshed=%s "
                    "failed=%s "
                    "after_id=%s"
                ),
                batches,
                len(assets),
                scanned,
                refreshed,
                failed,
                after_id,
            )

        result = {
            "scanned": scanned,
            "refreshed": refreshed,
            "failed": failed,
            "batches": batches,
        }

        logger.info(
            (
                "asset_risk_refresh_complete "
                "scanned=%s "
                "refreshed=%s "
                "failed=%s "
                "batches=%s"
            ),
            scanned,
            refreshed,
            failed,
            batches,
        )

        return result
