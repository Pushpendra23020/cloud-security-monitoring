import json
from pathlib import Path

from app.pipeline.cloudtrail_pipeline import CloudTrailIngestionPipeline
from app.storage.json_event_store import JsonEventStore


def load_fixture(filename: str) -> dict:
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "aws"
        / filename
    )

    with fixture_path.open(encoding="utf-8") as file:
        return json.load(file)


def test_batch_processes_multiple_events(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    events = [
        load_fixture("cloudtrail_console_login.json"),
        load_fixture("cloudtrail_failed_login.json"),
    ]

    result = pipeline.process_batch(events)

    assert result["processed"] == 2
    assert result["saved"] == 2
    assert result["duplicates"] == 0
    assert result["failed"] == 0

    stored_events = store.get_all()

    assert len(stored_events) == 2


def test_batch_continues_after_bad_event(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    good_event = load_fixture(
        "cloudtrail_console_login.json"
    )

    bad_event = {
        "eventID": "bad-event-001",
        "eventName": "BrokenEvent",
        "eventSource": "iam.amazonaws.com"
    }

    second_good_event = load_fixture(
        "cloudtrail_failed_login.json"
    )

    events = [
        good_event,
        bad_event,
        second_good_event,
    ]

    result = pipeline.process_batch(events)

    assert result["processed"] == 3
    assert result["saved"] == 2
    assert result["failed"] == 1

    assert len(result["errors"]) == 1
    assert result["errors"][0]["event_id"] == "bad-event-001"

    stored_events = store.get_all()

    assert len(stored_events) == 2


def test_batch_detects_duplicates(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    event = load_fixture(
        "cloudtrail_console_login.json"
    )

    events = [
        event,
        event,
    ]

    result = pipeline.process_batch(events)

    assert result["processed"] == 2
    assert result["saved"] == 1
    assert result["duplicates"] == 1
    assert result["failed"] == 0
