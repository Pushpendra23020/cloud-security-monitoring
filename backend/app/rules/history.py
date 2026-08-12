from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict, Iterable, List, Tuple

from app.models.security_event import SecurityEvent


class EventHistoryBuffer:
    def __init__(
        self,
        retention_minutes: int = 60,
    ):
        self.retention = timedelta(
            minutes=retention_minutes
        )

        self._events: Deque[SecurityEvent] = deque()

    def add(
        self,
        event: SecurityEvent,
    ) -> None:
        self._events.append(event)

        self._purge_old_events(
            reference_time=event.timestamp
        )

    def _purge_old_events(
        self,
        reference_time: datetime,
    ) -> None:
        cutoff = reference_time - self.retention

        while self._events:
            oldest = self._events[0]

            if oldest.timestamp >= cutoff:
                break

            self._events.popleft()

    def get_events(
        self,
    ) -> List[SecurityEvent]:
        return list(self._events)

    def find(
        self,
        *,
        event_name: str | None = None,
        service: str | None = None,
        source_ip: str | None = None,
        user_identity: str | None = None,
        since: datetime | None = None,
    ) -> List[SecurityEvent]:
        matches: List[SecurityEvent] = []

        for event in self._events:
            if (
                event_name is not None
                and event.event_name != event_name
            ):
                continue

            if (
                service is not None
                and event.service != service
            ):
                continue

            if (
                source_ip is not None
                and event.source_ip != source_ip
            ):
                continue

            if (
                user_identity is not None
                and event.user_identity != user_identity
            ):
                continue

            if (
                since is not None
                and event.timestamp < since
            ):
                continue

            matches.append(event)

        return matches

    def group_by_source_ip(
        self,
        events: Iterable[SecurityEvent] | None = None,
    ) -> Dict[str, List[SecurityEvent]]:
        grouped: Dict[str, List[SecurityEvent]] = defaultdict(list)

        selected_events = (
            list(events)
            if events is not None
            else list(self._events)
        )

        for event in selected_events:
            if event.source_ip:
                grouped[event.source_ip].append(event)

        return dict(grouped)

    def group_by_user(
        self,
        events: Iterable[SecurityEvent] | None = None,
    ) -> Dict[str, List[SecurityEvent]]:
        grouped: Dict[str, List[SecurityEvent]] = defaultdict(list)

        selected_events = (
            list(events)
            if events is not None
            else list(self._events)
        )

        for event in selected_events:
            if event.user_identity:
                grouped[event.user_identity].append(event)

        return dict(grouped)

    def count_by_source_ip(
        self,
        events: Iterable[SecurityEvent] | None = None,
    ) -> Dict[str, int]:
        grouped = self.group_by_source_ip(events)

        return {
            source_ip: len(items)
            for source_ip, items in grouped.items()
        }

    def count_by_user(
        self,
        events: Iterable[SecurityEvent] | None = None,
    ) -> Dict[str, int]:
        grouped = self.group_by_user(events)

        return {
            user: len(items)
            for user, items in grouped.items()
        }
