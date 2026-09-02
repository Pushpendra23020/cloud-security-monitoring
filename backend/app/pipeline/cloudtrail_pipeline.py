from app.repositories.asset_repository import AssetRepository
import logging
from typing import Any, Dict, Iterable
from app.services.asset_risk_service import AssetRiskService
from app.database.session import SessionLocal, set_tenant_context
from app.normalizers.aws.cloudtrail import normalize_cloudtrail_event
from app.pipeline.detection_pipeline import DetectionPipeline
from app.pipeline.event_classifier import classify_event
from app.pipeline.event_validator import validate_event
from app.services.asset_discovery_service import AssetDiscoveryService
from app.storage.json_event_store import JsonEventStore
from app.core.tenancy import DEFAULT_ORGANIZATION_ID
from app.models.security_event import SecurityEvent


logger = logging.getLogger(__name__)


class CloudTrailIngestionPipeline:
    def __init__(
        self,
        store: JsonEventStore | None = None,
        detection_pipeline: DetectionPipeline | None = None,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
        persist_events: bool = True,
    ):
        self.organization_id = organization_id
        self.store = (
            store
            or (JsonEventStore(organization_id=organization_id) if persist_events else None)
        )

        self.detection_pipeline = (
            detection_pipeline
            or DetectionPipeline(
                organization_id=organization_id,
            )
        )

    def _discover_asset(
        self,
        event,
    ) -> None:
        """
        Discover or refresh an asset from a normalized
        cloud security event.

        Asset discovery is intentionally non-fatal:
        failure to update inventory must not stop
        security event ingestion or detection.
        """

        if not event.resource_id:
            return

        if not event.resource_type:
            return

        db = SessionLocal()
        set_tenant_context(db, self.organization_id)

        try:
            asset = (
                AssetDiscoveryService
                .discover_from_event(
                    db=db,
                    event=event,
                    organization_id=self.organization_id,
                )
            )

            if asset is not None:
                logger.info(
                    (
                        "asset_discovered "
                        "asset_id=%s "
                        "asset_type=%s "
                        "cloud_account_id=%s "
                        "region=%s"
                    ),
                    asset.asset_id,
                    asset.asset_type,
                    asset.cloud_account_id,
                    asset.region,
                )

        except Exception:
            db.rollback()

            logger.exception(
                (
                    "asset_discovery_failed "
                    "event_id=%s "
                    "resource_type=%s "
                    "resource_id=%s"
                ),
                event.event_id,
                event.resource_type,
                event.resource_id,
            )

        finally:
            db.close()
    def _recalculate_asset_risk(
        self,
        event,
    ) -> None:
        """
        Recalculate only the asset referenced
        by the current security event.

        Risk calculation is non-fatal so a
        scoring failure cannot stop ingestion.
        """

        if not event.resource_id:
            return

        db = SessionLocal()
        set_tenant_context(db, self.organization_id)

        try:
            from app.repositories.asset_repository import (
                AssetRepository,
            )

            asset = (
                AssetRepository.get_by_asset_id(
                    db=db,
                    asset_id=event.resource_id,
                    organization_id=self.organization_id,
                )
            )

            if asset is None:
                return

            AssetRiskService.enrich_asset(
                db=db,
                asset=asset,
            )

            logger.info(
                (
                    "asset_risk_recalculated "
                    "asset_id=%s "
                    "risk_score=%s "
                    "risk_level=%s "
                    "alerts_count=%s "
                    "findings_count=%s"
                ),
                asset.asset_id,
                asset.risk_score,
                asset.risk_level,
                asset.alerts_count,
                asset.findings_count,
            )

        except Exception:
            db.rollback()

            logger.exception(
                (
                    "asset_risk_recalculation_failed "
                    "event_id=%s "
                    "resource_id=%s"
                ),
                event.event_id,
                event.resource_id,
            )

        finally:
            db.close()

    def process(
        self,
        raw_event: Dict[str, Any],
    ) -> bool:
        #
        # 1. Normalize raw CloudTrail event.
        #
        event = normalize_cloudtrail_event(
            raw_event
        )

        #
        # 2. Validate normalized event.
        #
        event = validate_event(event)

        #
        # 3. Classify event severity/category.
        #
        event = classify_event(event)

        return self.process_normalized(event)

    def process_normalized(
        self,
        event: SecurityEvent,
        *,
        persist: bool = True,
    ) -> bool:
        """Run enrichment and detection for a normalized durable event."""

        if persist and self.store is None:
            raise RuntimeError("An event store is required when persistence is enabled.")
        saved = self.store.save(event) if persist else True

        if saved:
            #
            # 5. Automatically discover/update asset.
            #
            self._discover_asset(event)

            #
            # 6. Run detection pipeline.
            #
            alerts = (
                self.detection_pipeline
                .process(event)
            )
                        
            # 7. Recalculate security risk after
            # alerts from this event are persisted.
            
            self._recalculate_asset_risk(
                event
            )

            for alert in alerts:
                logger.warning(
                    (
                        "security_alert "
                        "rule_id=%s "
                        "rule_name=%s "
                        "severity=%s "
                        "event_id=%s "
                        "event_name=%s "
                        "resource_type=%s "
                        "resource_id=%s"
                    ),
                    alert.rule_id,
                    alert.rule_name,
                    alert.severity,
                    alert.event_id,
                    alert.event_name,
                    alert.resource_type,
                    alert.resource_id,
                )

            logger.info(
                (
                    "security_event_saved "
                    "event_id=%s "
                    "event_name=%s "
                    "severity=%s "
                    "resource_type=%s "
                    "resource_id=%s"
                ),
                event.event_id,
                event.event_name,
                event.severity,
                event.resource_type,
                event.resource_id,
            )

        else:
            logger.info(
                (
                    "security_event_duplicate "
                    "event_id=%s "
                    "event_name=%s"
                ),
                event.event_id,
                event.event_name,
            )

        return saved

    def process_batch(
        self,
        raw_events: Iterable[
            Dict[str, Any]
        ],
    ) -> dict:
        result = {
            "processed": 0,
            "saved": 0,
            "duplicates": 0,
            "failed": 0,
            "errors": [],
        }

        for index, raw_event in enumerate(
            raw_events
        ):
            result["processed"] += 1

            try:
                saved = self.process(
                    raw_event
                )

                if saved:
                    result["saved"] += 1

                else:
                    result["duplicates"] += 1

            except Exception as exc:
                result["failed"] += 1

                error_data = {
                    "index": index,
                    "event_id": (
                        raw_event.get(
                            "eventID"
                        )
                    ),
                    "event_name": (
                        raw_event.get(
                            "eventName"
                        )
                    ),
                    "error": str(exc),
                }

                result["errors"].append(
                    error_data
                )

                logger.exception(
                    (
                        "security_event_failed "
                        "index=%s "
                        "event_id=%s "
                        "event_name=%s"
                    ),
                    index,
                    raw_event.get(
                        "eventID"
                    ),
                    raw_event.get(
                        "eventName"
                    ),
                )

        logger.info(
            (
                "cloudtrail_batch_complete "
                "processed=%s "
                "saved=%s "
                "duplicates=%s "
                "failed=%s"
            ),
            result["processed"],
            result["saved"],
            result["duplicates"],
            result["failed"],
        )

        return result
