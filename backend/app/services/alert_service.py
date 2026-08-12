from typing import Iterable, List

from app.models.alert import Alert
from app.storage.json_alert_store import JsonAlertStore


class AlertService:
    def __init__(
        self,
        store: JsonAlertStore | None = None,
    ):
        self.store = store or JsonAlertStore()

    def save_alert(
        self,
        alert: Alert,
    ) -> bool:
        return self.store.save(alert)

    def save_alerts(
        self,
        alerts: Iterable[Alert],
    ) -> int:
        saved_count = 0

        for alert in alerts:
            if self.save_alert(alert):
                saved_count += 1

        return saved_count

    def get_all_alerts(
        self,
    ) -> List[Alert]:
        return self.store.load_all()
