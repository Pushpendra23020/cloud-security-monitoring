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


logger = logging.getLogger(__name__)


class CloudTrailIngestionService:
    def __init__(
        self,
        collector,
        store: JsonEventStore | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ):
        self.collector = collector
        self.pipeline = CloudTrailIngestionPipeline(store)

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

        result = self.pipeline.process_batch(
            raw_events
        )

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
