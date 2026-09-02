import logging
from datetime import datetime, timedelta, timezone

from app.collectors.aws.cloudtrail_parser import (
    parse_lookup_events,
)
from app.pipeline.cloudtrail_pipeline import (
    CloudTrailIngestionPipeline,
)
from app.storage.checkpoint_store import (
    CheckpointStore,
)
from app.storage.json_event_store import (
    JsonEventStore,
)
from app.utils.metrics import CLOUDTRAIL_EVENTS_TOTAL
from app.pipeline.detection_pipeline import DetectionPipeline
from app.repositories.event_queue_repository import EventQueueRepository
from app.config import settings

logger = logging.getLogger(__name__)


class CloudTrailIngestionService:
    def __init__(
        self,
        collector,
        *,
        organization_id: int,
        store: JsonEventStore | None = None,
        checkpoint_store: CheckpointStore | None = None,
        detection_pipeline: DetectionPipeline | None = None,
        queue_repository: EventQueueRepository | None = None,
    ):
        self.collector = collector
        self.queue_repository = queue_repository
        self.pipeline = (
            None
            if queue_repository is not None
            else CloudTrailIngestionPipeline(
                store,
                detection_pipeline,
                organization_id=organization_id,
            )
        )

        self.checkpoint_store = (
            checkpoint_store
            or CheckpointStore()
        )

    def collect_and_ingest(
        self,
        lookback_minutes: int = 60,
    ) -> dict:
        end_time = datetime.now(timezone.utc)

        checkpoint = (
            self.checkpoint_store
            .get_last_checkpoint()
        )

        if checkpoint is None:
            start_time = end_time - timedelta(
                minutes=lookback_minutes
            )
        else:
            start_time = checkpoint

        logger.info(
            (
                "cloudtrail_collection_start "
                "start_time=%s end_time=%s"
            ),
            start_time.isoformat(),
            end_time.isoformat(),
        )

        lookup_events = self.collector.collect_events(
            start_time=start_time,
            end_time=end_time,
        )

        raw_events = parse_lookup_events(
            lookup_events
        )

        if self.queue_repository is not None:
            result = self.queue_repository.enqueue_batch(
                raw_events,
                source="cloudtrail",
                max_attempts=settings.EVENT_QUEUE_MAX_ATTEMPTS,
            )
        else:
            result = self.pipeline.process_batch(raw_events)
        for metric_result, count in (
            ("processed", result["processed"]),
            ("saved", result["saved"]),
            ("duplicate", result["duplicates"]),
            ("failed", result["failed"]),
        ):
            CLOUDTRAIL_EVENTS_TOTAL.labels(
                result=metric_result,
            ).inc(count)

        if result["failed"] == 0:
            self.checkpoint_store.save_checkpoint(
                end_time
            )

            logger.info(
                "cloudtrail_checkpoint_saved checkpoint=%s",
                end_time.isoformat(),
            )
        else:
            logger.warning(
                (
                    "cloudtrail_checkpoint_not_updated "
                    "failed_events=%s"
                ),
                result["failed"],
            )

        logger.info(
            (
                "cloudtrail_ingestion_complete "
                "processed=%s saved=%s "
                "duplicates=%s failed=%s"
            ),
            result["processed"],
            result["saved"],
            result["duplicates"],
            result["failed"],
        )

        return result
