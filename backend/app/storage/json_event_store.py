import json
from pathlib import Path
from typing import List

from app.models.security_event import SecurityEvent


class JsonEventStore:
    def __init__(self, file_path: str = "data/normalized/security_events.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def event_exists(self, event_id: str) -> bool:
        if not self.file_path.exists():
            return False

        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                stored_event = json.loads(line)

                if stored_event.get("event_id") == event_id:
                    return True

        return False

    def save(self, event: SecurityEvent) -> bool:
        if self.event_exists(event.event_id):
            return False

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    event.model_dump(mode="json"),
                    ensure_ascii=False,
                )
                + "\n"
            )

        return True

    def get_all(self) -> List[dict]:
        if not self.file_path.exists():
            return []

        events = []

        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line:
                    events.append(json.loads(line))

        return events
