from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.alert import Alert as AlertDB
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository


class PostgresAlertRepository(AlertRepository):
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

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

        db_alert = self._to_db_model(alert)

        self.session.add(db_alert)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False

        return True

    def get(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        statement = select(AlertDB).where(
            AlertDB.alert_id == alert_id
        )

        db_alert = self.session.execute(
            statement
        ).scalar_one_or_none()

        if db_alert is None:
            return None

        return self._to_domain_model(
            db_alert
        )

    def update(
        self,
        alert: Alert,
    ) -> bool:
        statement = select(AlertDB).where(
            AlertDB.alert_id == alert.alert_id
        )

        db_alert = self.session.execute(
            statement
        ).scalar_one_or_none()

        if db_alert is None:
            return False

        self._update_db_model(
            db_alert,
            alert,
        )

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False

        return True

    def load_all(
        self,
    ) -> List[Alert]:
        statement = select(AlertDB).order_by(
            AlertDB.created_at.desc()
        )

        db_alerts = self.session.execute(
            statement
        ).scalars().all()

        return [
            self._to_domain_model(db_alert)
            for db_alert in db_alerts
        ]

    def exists(
        self,
        alert_id: str,
    ) -> bool:
        statement = select(
            AlertDB.id
        ).where(
            AlertDB.alert_id == alert_id
        )

        result = self.session.execute(
            statement
        ).scalar_one_or_none()

        return result is not None

    def detection_exists(
        self,
        detection_key: str,
    ) -> bool:
        statement = select(
            AlertDB.id
        ).where(
            AlertDB.detection_key
            == detection_key
        )

        result = self.session.execute(
            statement
        ).scalar_one_or_none()

        return result is not None


    def get_by_fingerprint(
        self,
        fingerprint: str,
    ) -> Optional[Alert]:
        statement = select(AlertDB).where(
            AlertDB.fingerprint == fingerprint
        ).order_by(
            AlertDB.created_at.desc()
        )

        db_alert = self.session.execute(
            statement
        ).scalars().first()

        if db_alert is None:
            return None

        return self._to_domain_model(
            db_alert
        )

    @staticmethod
    def _to_db_model(
        alert: Alert,
    ) -> AlertDB:
        return AlertDB(
            alert_id=alert.alert_id,
            rule_id=alert.rule_id,
            rule_name=alert.rule_name,
            description=alert.description,
            severity=alert.severity.value,
            event_id=alert.event_id,
            event_name=alert.event_name,
            detection_key=alert.detection_key,
            fingerprint=alert.fingerprint,
            occurrence_count=alert.occurrence_count,
            cloud_provider=alert.cloud_provider,
            account_id=alert.account_id,
            region=alert.region,
            service=alert.service,
            source_ip=alert.source_ip,
            user_identity=alert.user_identity,
            incident_id=alert.incident_id,
            status=alert.status.value,
            mitre_tactic=alert.mitre_tactic,
            mitre_technique=alert.mitre_technique,
            mitre_technique_id=(
                alert.mitre_technique_id
            ),
            metadata_json=alert.metadata,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            acknowledged_at=(
                alert.acknowledged_at
            ),
            resolved_at=alert.resolved_at,
            first_seen_at=alert.first_seen_at,
            last_seen_at=alert.last_seen_at,
            notification_status=(
                alert.notification_status.value
            ),
            last_notified_at=(
                alert.last_notified_at
            ),
            suppressed_until=(
                alert.suppressed_until
            ),
            resource_type=alert.resource_type,
            resource_id=alert.resource_id,
        )

    @staticmethod
    def _to_domain_model(
        db_alert: AlertDB,
    ) -> Alert:
        return Alert(
            alert_id=db_alert.alert_id,
            rule_id=db_alert.rule_id,
            rule_name=db_alert.rule_name,
            description=db_alert.description,
            severity=db_alert.severity,
            event_id=db_alert.event_id,
            event_name=db_alert.event_name,
            detection_key=db_alert.detection_key,
            fingerprint=db_alert.fingerprint,
            occurrence_count=db_alert.occurrence_count,
            cloud_provider=db_alert.cloud_provider,
            account_id=db_alert.account_id,
            region=db_alert.region,
            service=db_alert.service,
            source_ip=db_alert.source_ip,
            user_identity=db_alert.user_identity,
            incident_id=db_alert.incident_id,
            status=db_alert.status,
            mitre_tactic=db_alert.mitre_tactic,
            mitre_technique=db_alert.mitre_technique,
            mitre_technique_id=(
                db_alert.mitre_technique_id
            ),
            metadata=(
                db_alert.metadata_json or {}
            ),
            created_at=db_alert.created_at,
            updated_at=db_alert.updated_at,
            acknowledged_at=(
                db_alert.acknowledged_at
            ),
            resolved_at=db_alert.resolved_at,
            first_seen_at=db_alert.first_seen_at,
            last_seen_at=db_alert.last_seen_at,
            notification_status=(
                db_alert.notification_status
            ),
            last_notified_at=(
                db_alert.last_notified_at
            ),
            suppressed_until=(
                db_alert.suppressed_until
            ),
            resource_type=db_alert.resource_type,
            resource_id=db_alert.resource_id,
        )

    @staticmethod
    def _update_db_model(
        db_alert: AlertDB,
        alert: Alert,
    ) -> None:
        db_alert.rule_id = alert.rule_id
        db_alert.rule_name = alert.rule_name
        db_alert.description = alert.description
        db_alert.severity = alert.severity.value

        db_alert.event_id = alert.event_id
        db_alert.event_name = alert.event_name
        db_alert.detection_key = (
            alert.detection_key
        )
        db_alert.fingerprint = alert.fingerprint
        db_alert.occurrence_count = (
            alert.occurrence_count
        )

        db_alert.cloud_provider = (
            alert.cloud_provider
        )
        db_alert.account_id = alert.account_id
        db_alert.region = alert.region
        db_alert.service = alert.service

        db_alert.source_ip = alert.source_ip
        db_alert.user_identity = (
            alert.user_identity
        )

        db_alert.incident_id = alert.incident_id

        db_alert.status = alert.status.value

        db_alert.mitre_tactic = (
            alert.mitre_tactic
        )
        db_alert.mitre_technique = (
            alert.mitre_technique
        )
        db_alert.mitre_technique_id = (
            alert.mitre_technique_id
        )

        db_alert.metadata_json = alert.metadata

        db_alert.created_at = alert.created_at
        db_alert.updated_at = alert.updated_at

        db_alert.acknowledged_at = (
            alert.acknowledged_at
        )
        db_alert.resolved_at = (
            alert.resolved_at
        )

        db_alert.first_seen_at = (
            alert.first_seen_at
        )
        db_alert.last_seen_at = (
            alert.last_seen_at
        )
        db_alert.notification_status = (
            alert.notification_status.value
        )
        db_alert.last_notified_at = (
            alert.last_notified_at
        )
        db_alert.suppressed_until = (
            alert.suppressed_until
        )

        db_alert.resource_type = alert.resource_type
        db_alert.resource_id = alert.resource_id

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
        filters = []

        if severity is not None:
            filters.append(
                AlertDB.severity == severity
            )

        if status is not None:
            filters.append(
                AlertDB.status == status
            )

        if cloud_provider is not None:
            filters.append(
                AlertDB.cloud_provider
                == cloud_provider
            )

        if account_id is not None:
            filters.append(
                AlertDB.account_id
                == account_id
            )

        count_statement = select(
            func.count(AlertDB.id)
        )

        if filters:
            count_statement = (
                count_statement.where(*filters)
            )

        total = self.session.execute(
            count_statement
        ).scalar_one()

        allowed_sort_fields = {
            "created_at": AlertDB.created_at,
            "updated_at": AlertDB.updated_at,
            "severity": AlertDB.severity,
            "status": AlertDB.status,
            "rule_id": AlertDB.rule_id,
        }

        sort_column = allowed_sort_fields.get(
            sort_by,
            AlertDB.created_at,
        )

        if sort_order == "asc":
            ordering = sort_column.asc()
        else:
            ordering = sort_column.desc()

        statement = (
            select(AlertDB)
            .where(*filters)
            .order_by(ordering)
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        db_alerts = self.session.execute(
            statement
        ).scalars().all()

        alerts = [
            self._to_domain_model(db_alert)
            for db_alert in db_alerts
        ]

        return alerts, total

    def get_statistics(
        self,
    ) -> dict[str, int]:
        status_rows = self.session.execute(
            select(
                AlertDB.status,
                func.count(AlertDB.id),
            ).group_by(
                AlertDB.status
            )
        ).all()

        severity_rows = self.session.execute(
            select(
                AlertDB.severity,
                func.count(AlertDB.id),
            ).group_by(
                AlertDB.severity
            )
        ).all()

        total = self.session.execute(
            select(
                func.count(AlertDB.id)
            )
        ).scalar_one()

        stats = {
            "total": total,
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

        for status_value, count in status_rows:
            if status_value in stats:
                stats[status_value] = count

        for severity_value, count in severity_rows:
            if severity_value in stats:
                stats[severity_value] = count

        return stats
    def get_by_incident_id(
        self,
        incident_id: str,
    ) -> List[Alert]:
        statement = (
            select(AlertDB)
            .where(
                AlertDB.incident_id
                == incident_id
            )
            .order_by(
                AlertDB.created_at.asc()
            )
        )

        rows = self.session.execute(
            statement
        ).scalars().all()

        return [
            self._to_domain_model(row)
            for row in rows
        ]
