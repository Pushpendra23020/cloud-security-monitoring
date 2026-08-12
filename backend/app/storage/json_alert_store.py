import json
from pathlib import Path
from typing import List

from app.models.alert import Alert


class JsonAlertStore:
    def __init__(
        self,
        file_path: str = "data/alerts/security_alerts.jsonl",
    ):
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file_path.exists():
            self.file_path.touch()

    def save(
        self,
        alert: Alert,
    ) -> bool:
        if self.exists(alert.alert_id):
            return False

        if (
            alert.detection_key
            and self.detection_exists(
                alert.detection_key
            )
        ):
            return False

        with self.file_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                alert.model_dump_json()
                + "\n"
            )

        return True

    def exists(
        self,
        alert_id: str,
    ) -> bool:
        for alert in self.load_all():
            if alert.alert_id == alert_id:
                return True

        return False

    def detection_exists(
        self,
        detection_key: str,
    ) -> bool:
        for alert in self.load_all():
            if (
                alert.detection_key
                == detection_key
            ):
                return True

        return False

    def load_all(
        self,
    ) -> List[Alert]:
        alerts: List[Alert] = []

        with self.file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                alerts.append(
                    Alert.model_validate(data)
                )

        return alerts
