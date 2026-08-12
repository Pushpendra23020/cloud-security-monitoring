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


def test_pipeline_processes_successful_login(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    raw_event = load_fixture(
        "cloudtrail_console_login.json"
    )

    saved = pipeline.process(raw_event)

    assert saved is True

    events = store.get_all()

    assert len(events) == 1

    event = events[0]

    assert event["cloud_provider"] == "aws"
    assert event["event_name"] == "ConsoleLogin"
    assert event["severity"] == "info"
    assert event["success"] is True


def test_pipeline_classifies_failed_login(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    raw_event = load_fixture(
        "cloudtrail_failed_login.json"
    )

    saved = pipeline.process(raw_event)

    assert saved is True

    events = store.get_all()

    assert len(events) == 1

    event = events[0]

    assert event["event_name"] == "ConsoleLogin"
    assert event["severity"] == "medium"
    assert event["success"] is False
    assert event["error_code"] == "FailedAuthentication"


def test_pipeline_deduplicates_events(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    raw_event = load_fixture(
        "cloudtrail_console_login.json"
    )

    first_result = pipeline.process(raw_event)
    second_result = pipeline.process(raw_event)

    assert first_result is True
    assert second_result is False

    events = store.get_all()

    assert len(events) == 1
