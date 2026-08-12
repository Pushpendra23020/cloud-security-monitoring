import json

from app.services.cloudtrail_ingestion_service import (
    CloudTrailIngestionService,
)
from app.storage.json_event_store import JsonEventStore


class FakeCloudTrailCollector:
    def collect_events(
    self,
    lookback_minutes=60,
    max_results=50,
    start_time=None,
    end_time=None,
):
        cloudtrail_event = {
            "eventVersion": "1.08",
            "eventID": "integration-event-001",
            "eventTime": "2026-08-09T12:00:00Z",
            "eventSource": "signin.amazonaws.com",
            "eventName": "ConsoleLogin",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "203.0.113.25",
            "userIdentity": {
                "type": "IAMUser",
                "accountId": "123456789012",
                "userName": "integration-user",
            },
        }

        return [
            {
                "EventId": "integration-event-001",
                "EventName": "ConsoleLogin",
                "CloudTrailEvent": json.dumps(
                    cloudtrail_event
                ),
            }
        ]


def test_collector_to_pipeline_integration(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(
        str(storage_file)
    )

    collector = FakeCloudTrailCollector()

    service = CloudTrailIngestionService(
        collector=collector,
        store=store,
    )

    result = service.collect_and_ingest(
        lookback_minutes=60
    )

    assert result["processed"] == 1
    assert result["saved"] == 1
    assert result["duplicates"] == 0
    assert result["failed"] == 0

    events = store.get_all()

    assert len(events) == 1

    event = events[0]

    assert event["event_id"] == "integration-event-001"
    assert event["cloud_provider"] == "aws"
    assert event["event_name"] == "ConsoleLogin"
    assert event["user_identity"] == "integration-user"
