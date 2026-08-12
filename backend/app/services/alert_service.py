from datetime import datetime, timezone
from typing import List, Optional

from app.models.alert import (
    Alert,
    AlertStatus,
)
from app.repositories.alert_repository import (
    AlertRepository,
)
from app.storage.json_alert_store import (
    JsonAlertStore,
)
from app.services.status_transition import (
    validate_transition,
)


class AlertService:
    ALERT_TRANSITIONS = {
        AlertStatus.OPEN: {
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.INVESTIGATING,
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
        },
        AlertStatus.ACKNOWLEDGED: {
            AlertStatus.INVESTIGATING,
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
        },
        AlertStatus.INVESTIGATING: {
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
        },
        AlertStatus.RESOLVED: set(),
        AlertStatus.FALSE_POSITIVE: set(),
    }

    def __init__(
        self,
        repository: AlertRepository | None = None,
    ):
        self.repository = (
            repository or JsonAlertStore()
        )

    def save_alert(
        self,
        alert: Alert,
    ) -> bool:
        return self.repository.save(alert)

    def update_alert(
        self,
        alert: Alert,
    ) -> bool:
        return self.repository.update(alert)

    def save_alerts(
        self,
        alerts: List[Alert],
    ) -> int:
        saved = 0

        for alert in alerts:
            if self.save_alert(alert):
                saved += 1

        return saved

    def get_all_alerts(
        self,
    ) -> List[Alert]:
        return self.repository.load_all()

    def get_alert(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        return self.repository.get(alert_id)

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
    ):
        return self.repository.list_alerts(
            severity=severity,
            status=status,
            cloud_provider=cloud_provider,
            account_id=account_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_statistics(
        self,
    ) -> dict[str, int]:
        return self.repository.get_statistics()

    def acknowledge_alert(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        validate_transition(
            alert.status,
            AlertStatus.ACKNOWLEDGED,
            self.ALERT_TRANSITIONS,
        )

        now = datetime.now(timezone.utc)

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = now
        alert.updated_at = now

        self.repository.update(alert)

        return alert

    def investigate_alert(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        validate_transition(
            alert.status,
            AlertStatus.INVESTIGATING,
            self.ALERT_TRANSITIONS,
        )

        alert.status = AlertStatus.INVESTIGATING
        alert.updated_at = datetime.now(
            timezone.utc
        )

        self.repository.update(alert)

        return alert

    def resolve_alert(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        validate_transition(
            alert.status,
            AlertStatus.RESOLVED,
            self.ALERT_TRANSITIONS,
        )

        now = datetime.now(timezone.utc)

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = now
        alert.updated_at = now

        self.repository.update(alert)

        return alert

    def mark_false_positive(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        validate_transition(
            alert.status,
            AlertStatus.FALSE_POSITIVE,
            self.ALERT_TRANSITIONS,
        )

        now = datetime.now(timezone.utc)

        alert.status = (
            AlertStatus.FALSE_POSITIVE
        )
        alert.resolved_at = now
        alert.updated_at = now

        self.repository.update(alert)

        return alert
