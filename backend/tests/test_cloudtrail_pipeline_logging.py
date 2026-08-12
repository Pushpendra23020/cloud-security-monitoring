import json
import logging
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


def test_pipeline_logs_saved_event(tmp_path, caplog):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    raw_event = load_fixture(
        "cloudtrail_console_login.json"
    )

    with caplog.at_level(logging.INFO):
        pipeline.process(raw_event)

    assert "security_event_saved" in caplog.text
    assert "ConsoleLogin" in caplog.text


def test_pipeline_logs_duplicate(tmp_path, caplog):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    raw_event = load_fixture(
        "cloudtrail_console_login.json"
    )

    pipeline.process(raw_event)

    with caplog.at_level(logging.INFO):
        pipeline.process(raw_event)

    assert "security_event_duplicate" in caplog.text


def test_batch_logs_failure(tmp_path, caplog):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))
    pipeline = CloudTrailIngestionPipeline(store)

    bad_event = {
        "eventID": "broken-event-001",
        "eventName": "BrokenEvent",
        "eventSource": "iam.amazonaws.com",
    }

    with caplog.at_level(logging.ERROR):
        result = pipeline.process_batch([bad_event])

    assert result["failed"] == 1
    assert "security_event_failed" in caplog.text
