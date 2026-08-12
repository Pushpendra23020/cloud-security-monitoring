import logging
from typing import Any, Dict, Iterable

from app.normalizers.aws.cloudtrail import normalize_cloudtrail_event
from app.pipeline.detection_pipeline import DetectionPipeline
from app.pipeline.event_classifier import classify_event
from app.pipeline.event_validator import validate_event
from app.storage.json_event_store import JsonEventStore

logger = logging.getLogger(__name__)


class CloudTrailIngestionPipeline:
    def __init__(
        self,
        store: JsonEventStore | None = None,
        detection_pipeline: DetectionPipeline | None = None,
    ):
        self.store = store or JsonEventStore()
        self.detection_pipeline = (
            detection_pipeline or DetectionPipeline()
        )

    def process(self, raw_event: Dict[str, Any]) -> bool:
        event = normalize_cloudtrail_event(raw_event)
        event = validate_event(event)
        event = classify_event(event)

        saved = self.store.save(event)

        if saved:
            alerts = self.detection_pipeline.process(event)

            for alert in alerts:
                logger.warning(
                    (
                        "security_alert rule_id=%s "
                        "rule_name=%s severity=%s "
                        "event_id=%s event_name=%s"
                    ),
                    alert.rule_id,
                    alert.rule_name,
                    alert.severity,
                    alert.event_id,
                    alert.event_name,
                )

            logger.info(
                "security_event_saved event_id=%s event_name=%s severity=%s",
                event.event_id,
                event.event_name,
                event.severity,
            )

        else:
            logger.info(
                "security_event_duplicate event_id=%s event_name=%s",
                event.event_id,
                event.event_name,
            )

        return saved

    def process_batch(
        self,
        raw_events: Iterable[Dict[str, Any]],
    ) -> dict:
        result = {
            "processed": 0,
            "saved": 0,
            "duplicates": 0,
            "failed": 0,
            "errors": [],
        }

        for index, raw_event in enumerate(raw_events):
            result["processed"] += 1

            try:
                saved = self.process(raw_event)

                if saved:
                    result["saved"] += 1
                else:
                    result["duplicates"] += 1

            except Exception as exc:
                result["failed"] += 1

                error_data = {
                    "index": index,
                    "event_id": raw_event.get("eventID"),
                    "event_name": raw_event.get("eventName"),
                    "error": str(exc),
                }

                result["errors"].append(error_data)

                logger.exception(
                    "security_event_failed index=%s event_id=%s event_name=%s",
                    index,
                    raw_event.get("eventID"),
                    raw_event.get("eventName"),
                )

        logger.info(
            (
                "cloudtrail_batch_complete "
                "processed=%s saved=%s duplicates=%s failed=%s"
            ),
            result["processed"],
            result["saved"],
            result["duplicates"],
            result["failed"],
        )

        return result       
