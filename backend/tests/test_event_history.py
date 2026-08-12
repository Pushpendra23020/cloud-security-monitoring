from datetime import datetime, timedelta, timezone

from app.models.security_event import SecurityEvent
from app.rules.history import EventHistoryBuffer


BASE_TIME = datetime(
    2026,
    8,
    12,
    10,
    0,
    tzinfo=timezone.utc,
)


def build_event(
    *,
    event_id: str,
    minutes: int = 0,
    event_name: str = "ConsoleLogin",
    service: str = "signin",
    source_ip: str = "192.0.2.10",
    user_identity: str = "test-user",
) -> SecurityEvent:
    return SecurityEvent(
        event_id=event_id,
        timestamp=BASE_TIME + timedelta(minutes=minutes),
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service=service,
        event_name=event_name,
        source_ip=source_ip,
        user_identity=user_identity,
        raw_event={},
    )


def test_add_event():
    history = EventHistoryBuffer()

    event = build_event(
        event_id="event-1"
    )

    history.add(event)

    events = history.get_events()

    assert len(events) == 1
    assert events[0].event_id == "event-1"


def test_old_events_are_removed():
    history = EventHistoryBuffer(
        retention_minutes=10
    )

    history.add(
        build_event(
            event_id="old",
            minutes=0,
        )
    )

    history.add(
        build_event(
            event_id="new",
            minutes=20,
        )
    )

    events = history.get_events()

    assert len(events) == 1
    assert events[0].event_id == "new"


def test_find_by_event_name():
    history = EventHistoryBuffer()

    history.add(
        build_event(
            event_id="event-1",
            event_name="ConsoleLogin",
        )
    )

    history.add(
        build_event(
            event_id="event-2",
            event_name="CreateUser",
            service="iam",
        )
    )

    results = history.find(
        event_name="ConsoleLogin"
    )

    assert len(results) == 1
    assert results[0].event_id == "event-1"


def test_find_by_source_ip():
    history = EventHistoryBuffer()

    history.add(
        build_event(
            event_id="event-1",
            source_ip="192.0.2.10",
        )
    )

    history.add(
        build_event(
            event_id="event-2",
            source_ip="198.51.100.20",
        )
    )

    results = history.find(
        source_ip="192.0.2.10"
    )

    assert len(results) == 1
    assert results[0].event_id == "event-1"


def test_find_since():
    history = EventHistoryBuffer()

    history.add(
        build_event(
            event_id="event-1",
            minutes=0,
        )
    )

    history.add(
        build_event(
            event_id="event-2",
            minutes=8,
        )
    )

    results = history.find(
        since=BASE_TIME + timedelta(minutes=5)
    )

    assert len(results) == 1
    assert results[0].event_id == "event-2"


def test_group_by_source_ip():
    history = EventHistoryBuffer()

    history.add(
        build_event(
            event_id="event-1",
            source_ip="192.0.2.10",
        )
    )

    history.add(
        build_event(
            event_id="event-2",
            source_ip="192.0.2.10",
        )
    )

    history.add(
        build_event(
            event_id="event-3",
            source_ip="198.51.100.20",
        )
    )

    grouped = history.group_by_source_ip()

    assert len(
        grouped["192.0.2.10"]
    ) == 2

    assert len(
        grouped["198.51.100.20"]
    ) == 1


def test_group_by_user():
    history = EventHistoryBuffer()

    history.add(
        build_event(
            event_id="event-1",
            user_identity="alice",
        )
    )

    history.add(
        build_event(
            event_id="event-2",
            user_identity="alice",
        )
    )

    history.add(
        build_event(
            event_id="event-3",
            user_identity="bob",
        )
    )

    grouped = history.group_by_user()

    assert len(grouped["alice"]) == 2
    assert len(grouped["bob"]) == 1


def test_count_by_source_ip():
    history = EventHistoryBuffer()

    history.add(
        build_event(
            event_id="event-1",
            source_ip="192.0.2.10",
        )
    )

    history.add(
        build_event(
            event_id="event-2",
            source_ip="192.0.2.10",
        )
    )

    counts = history.count_by_source_ip()

    assert counts["192.0.2.10"] == 2
