import logging
import os
import time
from sqlalchemy import select

from app.database.session import SessionLocal, set_tenant_context
from app.database.models.organization import Organization
from app.services.asset_risk_refresh_service import (
    AssetRiskRefreshService,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


REFRESH_INTERVAL_SECONDS = int(
    os.getenv(
        "ASSET_RISK_REFRESH_INTERVAL_SECONDS",
        "3600",
    )
)

STALE_MINUTES = int(
    os.getenv(
        "ASSET_RISK_STALE_MINUTES",
        "60",
    )
)

BATCH_SIZE = int(
    os.getenv(
        "ASSET_RISK_BATCH_SIZE",
        "100",
    )
)


def run_once() -> None:
    try:
        with SessionLocal() as discovery_db:
            organization_ids = list(
                discovery_db.scalars(
                    select(Organization.id).where(Organization.is_active.is_(True))
                )
            )
        for organization_id in organization_ids:
            with SessionLocal() as db:
                set_tenant_context(db, organization_id)
                result = AssetRiskRefreshService.refresh_stale(
                    db=db,
                    organization_id=organization_id,
                    batch_size=BATCH_SIZE,
                    stale_minutes=STALE_MINUTES,
                )

            logger.info(
                (
                    "risk_refresh_run "
                    "organization_id=%s "
                    "scanned=%s "
                    "refreshed=%s "
                    "failed=%s "
                    "batches=%s"
                ),
                organization_id,
                result["scanned"],
                result["refreshed"],
                result["failed"],
                result["batches"],
            )

    except Exception:
        logger.exception(
            "risk_refresh_run_failed"
        )


def main() -> None:
    logger.info(
        (
            "asset_risk_refresh_worker_started "
            "interval_seconds=%s "
            "stale_minutes=%s "
            "batch_size=%s"
        ),
        REFRESH_INTERVAL_SECONDS,
        STALE_MINUTES,
        BATCH_SIZE,
    )

    while True:
        run_once()

        time.sleep(
            REFRESH_INTERVAL_SECONDS
        )


if __name__ == "__main__":
    main()
