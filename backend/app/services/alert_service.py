from datetime import datetime, timezone
import hashlib
from typing import List, Optional

from app.models.alert import (
    Alert,
    AlertSeverity,
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
from app.database.session import SessionLocal
from app.repositories.asset_repository import AssetRepository
from app.services.asset_risk_service import AssetRiskService
from app.notifications.dispatcher import (
    NotificationDispatcher,
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
        dispatcher: NotificationDispatcher | None = None,
    ):
        self.repository = (
            repository or JsonAlertStore()
        )
        self.dispatcher = dispatcher

    SEVERITY_ORDER = [
        AlertSeverity.INFO,
        AlertSeverity.LOW,
        AlertSeverity.MEDIUM,
        AlertSeverity.HIGH,
        AlertSeverity.CRITICAL,
    ]

    ASSET_RISK_ESCALATION = {
        "low": 0,
        "medium": 0,
        "high": 1,
        "critical": 2,
    }

    @classmethod
    def calculate_effective_severity(
        cls,
        detection_severity: AlertSeverity,
        asset_risk_level: str | None,
    ) -> AlertSeverity:
        normalized_risk = str(
            asset_risk_level or "low"
        ).lower()

        escalation = (
            cls.ASSET_RISK_ESCALATION.get(
                normalized_risk,
                0,
            )
        )

        current_index = (
            cls.SEVERITY_ORDER.index(
                detection_severity
            )
        )

        final_index = min(
            current_index + escalation,
            len(cls.SEVERITY_ORDER) - 1,
        )

        return cls.SEVERITY_ORDER[
            final_index
        ]

    @staticmethod
    def generate_fingerprint(
        alert: Alert,
    ) -> str:
        parts = [
            alert.rule_id,
            alert.cloud_provider,
            alert.account_id or "",
            alert.region or "",
            alert.resource_type or "",
            alert.resource_id or "",
            alert.user_identity or "",
            alert.source_ip or "",
        ]

        raw = "|".join(parts)

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def _apply_asset_risk_severity(
        self,
        alert: Alert,
    ) -> None:
        if not alert.resource_id:
            return

        db = SessionLocal()

        try:
            asset = (
                AssetRepository.get_by_asset_id(
                    db=db,
                    asset_id=alert.resource_id,
                )
            )

            if asset is None:
                return

            original_severity = alert.severity

            effective_severity = (
                self.calculate_effective_severity(
                    detection_severity=(
                        original_severity
                    ),
                    asset_risk_level=(
                        asset.risk_level
                    ),
                )
            )

            alert.metadata[
                "detection_severity"
            ] = original_severity.value

            alert.metadata[
                "asset_risk_level"
            ] = asset.risk_level

            alert.metadata[
                "asset_risk_score"
            ] = asset.risk_score

            alert.metadata[
                "risk_adjusted"
            ] = (
                effective_severity
                != original_severity
            )

            alert.severity = (
                effective_severity
            )

        finally:
            db.close()

    def _dispatch_notification(
        self,
        alert: Alert,
    ) -> None:
        if self.dispatcher is None:
            return

        self.dispatcher.dispatch(
            alert
        )

        self.repository.update(
            alert
        )

    def save_alert(
        self,
        alert: Alert,
    ) -> bool:
        if self.repository.exists(
            alert.alert_id
        ):
            return False

        self._apply_asset_risk_severity(
            alert
        )

        if not alert.fingerprint:
            alert.fingerprint = (
                self.generate_fingerprint(alert)
            )

        existing = (
            self.repository.get_by_fingerprint(
                alert.fingerprint
            )
        )

        if (
            existing is not None
            and existing.status not in {
                AlertStatus.RESOLVED,
                AlertStatus.FALSE_POSITIVE,
            }
        ):
            now = datetime.now(timezone.utc)

            existing.occurrence_count += 1
            existing.last_seen_at = now
            existing.updated_at = now

            existing_index = (
                self.SEVERITY_ORDER.index(
                    existing.severity
                )
            )

            incoming_index = (
                self.SEVERITY_ORDER.index(
                    alert.severity
                )
            )

            if incoming_index > existing_index:
                existing.severity = alert.severity

                existing.metadata.update(
                    {
                        key: value
                        for key, value
                        in alert.metadata.items()
                        if key in {
                            "detection_severity",
                            "asset_risk_level",
                            "asset_risk_score",
                            "risk_adjusted",
                        }
                    }
                )

            updated = self.repository.update(
                existing
            )

            if updated:
                self._dispatch_notification(
                    existing
                )

            return updated

        now = datetime.now(timezone.utc)

        alert.first_seen_at = now
        alert.last_seen_at = now
        alert.updated_at = now

        saved = self.repository.save(
            alert
        )

        if saved:
            self._dispatch_notification(
                alert
            )

        return saved

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

        self._recalculate_linked_asset_risk(
            alert
        )

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

        self._recalculate_linked_asset_risk(
            alert
        )

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

        self._recalculate_linked_asset_risk(
            alert
        )

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

    def suppress_alert_notifications(
        self,
        alert_id: str,
        suppressed_until: datetime,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        now = datetime.now(timezone.utc)

        if suppressed_until.tzinfo is None:
            suppressed_until = (
                suppressed_until.replace(
                    tzinfo=timezone.utc
                )
            )

        if suppressed_until <= now:
            raise ValueError(
                "suppressed_until must be in the future"
            )

        from app.services.alert_notification_policy import (
            AlertNotificationPolicy,
        )

        AlertNotificationPolicy.suppress_until(
            alert,
            suppressed_until,
            now=now,
        )

        self.repository.update(
            alert
        )

        return alert

    def unsuppress_alert_notifications(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        now = datetime.now(timezone.utc)

        alert.suppressed_until = None

        from app.models.alert import (
            NotificationStatus,
        )

        alert.notification_status = (
            NotificationStatus.PENDING
        )
        alert.updated_at = now

        self.repository.update(
            alert
        )

        return alert

    def retry_notification(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)

        if alert is None:
            return None

        if self.dispatcher is None:
            return alert

        now = datetime.now(timezone.utc)

        # Manual analyst retry intentionally bypasses
        # the normal throttle window, but not an active
        # explicit suppression.
        if (
            alert.suppressed_until is not None
            and alert.suppressed_until > now
        ):
            return alert

        alert.last_notified_at = None

        self.dispatcher.dispatch(
            alert,
            now=now,
        )

        self.repository.update(
            alert
        )

        return alert

    def _recalculate_linked_asset_risk(
        self,
        alert: Alert,
    ) -> None:
        if not alert.resource_id:
            return

        db = SessionLocal()

        try:
            asset = (
                AssetRepository.get_by_asset_id(
                    db=db,
                    asset_id=alert.resource_id,
                )
            )

            if asset is None:
                return

            AssetRiskService.enrich_asset(
                db=db,
                asset=asset,
            )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()