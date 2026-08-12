from app.models.security_event import SecurityEvent
from app.storage.json_event_store import JsonEventStore


def test_save_event(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))

    event = SecurityEvent(
        event_id="event-001",
        cloud_provider="aws",
        event_name="ConsoleLogin",
        severity="info",
    )

    saved = store.save(event)

    assert saved is True
    assert storage_file.exists()

    events = store.get_all()

    assert len(events) == 1
    assert events[0]["event_id"] == "event-001"
    assert events[0]["event_name"] == "ConsoleLogin"


def test_duplicate_event_is_not_saved(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))

    event = SecurityEvent(
        event_id="event-duplicate",
        cloud_provider="aws",
        event_name="ConsoleLogin",
    )

    first_save = store.save(event)
    second_save = store.save(event)

    assert first_save is True
    assert second_save is False

    events = store.get_all()

    assert len(events) == 1


def test_multiple_events_are_saved(tmp_path):
    storage_file = tmp_path / "events.jsonl"

    store = JsonEventStore(str(storage_file))

    event1 = SecurityEvent(
        event_id="event-001",
        cloud_provider="aws",
        event_name="ConsoleLogin",
    )

    event2 = SecurityEvent(
        event_id="event-002",
        cloud_provider="aws",
        event_name="CreateAccessKey",
        severity="high",
    )

    assert store.save(event1) is True
    assert store.save(event2) is True

    events = store.get_all()

    assert len(events) == 2
