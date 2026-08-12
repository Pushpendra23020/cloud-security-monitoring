import json
from datetime import datetime, timezone

from app.services.cloudtrail_ingestion_service import (
    CloudTrailIngestionService,
)
from app.storage.checkpoint_store import CheckpointStore
from app.storage.json_event_store import JsonEventStore


class FakeIncrementalCollector:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def collect_events(
        self,
        start_time=None,
        end_time=None,
        **kwargs,
    ):
        self.start_time = start_time
        self.end_time = end_time

        raw_event = {
            "eventVersion": "1.08",
            "eventID": "incremental-001",
            "eventTime": "2026-08-12T10:00:00Z",
            "eventSource": "sts.amazonaws.com",
            "eventName": "GetCallerIdentity",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "203.0.113.10",
            "userIdentity": {
                "type": "IAMUser",
                "accountId": "123456789012",
                "userName": "test-user",
            },
        }

        return [
            {
                "EventId": "incremental-001",
                "EventName": "GetCallerIdentity",
                "CloudTrailEvent": json.dumps(raw_event),
            }
        ]


def test_existing_checkpoint_is_used(tmp_path):
    event_file = tmp_path / "events.jsonl"
    checkpoint_file = tmp_path / "checkpoint.json"

    event_store = JsonEventStore(str(event_file))
    checkpoint_store = CheckpointStore(
        str(checkpoint_file)
    )

    existing_checkpoint = datetime(
        2026,
        8,
        12,
        9,
        30,
        tzinfo=timezone.utc,
    )

    checkpoint_store.save_checkpoint(
        existing_checkpoint
    )

    collector = FakeIncrementalCollector()

    service = CloudTrailIngestionService(
        collector=collector,
        store=event_store,
        checkpoint_store=checkpoint_store,
    )

    result = service.collect_and_ingest(
        lookback_minutes=60
    )

    assert result["processed"] == 1
    assert result["saved"] == 1
    assert result["failed"] == 0

    assert collector.start_time == existing_checkpoint
    assert collector.end_time is not None

    new_checkpoint = (
        checkpoint_store.get_last_checkpoint()
    )

    assert new_checkpoint is not None
    assert new_checkpoint > existing_checkpoint
