import json
from pathlib import Path
from typing import List, Optional

from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository


class JsonAlertStore(AlertRepository):
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

    def get(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        for alert in self.load_all():
            if alert.alert_id == alert_id:
                return alert

        return None

    def update(
        self,
        updated_alert: Alert,
    ) -> bool:
        alerts = self.load_all()

        found = False

        for index, alert in enumerate(alerts):
            if alert.alert_id == updated_alert.alert_id:
                alerts[index] = updated_alert
                found = True
                break

        if not found:
            return False

        self._rewrite(alerts)

        return True

    def exists(
        self,
        alert_id: str,
    ) -> bool:
        return self.get(alert_id) is not None

    def detection_exists(
        self,
        detection_key: str,
    ) -> bool:
        for alert in self.load_all():
            if alert.detection_key == detection_key:
                return True

        return False


    def get_by_fingerprint(
        self,
        fingerprint: str,
    ) -> Optional[Alert]:
        for alert in self.load_all():
            if alert.fingerprint == fingerprint:
                return alert

        return None

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

    def list_alerts(
        self,
        *,
        severity: str | None = None,
        status: str | None = None,
        cloud_provider: str | None = None,
        account_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[List[Alert], int]:
        alerts = self.load_all()

        if severity is not None:
            alerts = [
                alert
                for alert in alerts
                if alert.severity.value == severity
            ]

        if status is not None:
            alerts = [
                alert
                for alert in alerts
                if alert.status.value == status
            ]

        if cloud_provider is not None:
            alerts = [
                alert
                for alert in alerts
                if alert.cloud_provider
                == cloud_provider
            ]

        if account_id is not None:
            alerts = [
                alert
                for alert in alerts
                if alert.account_id == account_id
            ]

        allowed_sort_fields = {
            "created_at",
            "updated_at",
            "severity",
            "status",
            "rule_id",
        }

        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        reverse = sort_order == "desc"

        alerts.sort(
            key=lambda alert: getattr(
                alert,
                sort_by,
            ),
            reverse=reverse,
        )

        total = len(alerts)

        start = (page - 1) * page_size
        end = start + page_size

        return alerts[start:end], total
    def _rewrite(
        self,
        alerts: List[Alert],
    ) -> None:
        with self.file_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            for alert in alerts:
                file.write(
                    alert.model_dump_json()
                    + "\n"
                )
    def get_statistics(
        self,
    ) -> dict[str, int]:
        alerts = self.load_all()

        stats = {
            "total": len(alerts),
            "open": 0,
            "acknowledged": 0,
            "investigating": 0,
            "resolved": 0,
            "false_positive": 0,
            "info": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }

        for alert in alerts:
            stats[alert.status.value] += 1
            stats[alert.severity.value] += 1

        return stats
    
    def get_by_incident_id(
        self,
        incident_id: str,
    ) -> List[Alert]:
        return [
            alert
            for alert in self.load_all()
            if alert.incident_id == incident_id
        ]