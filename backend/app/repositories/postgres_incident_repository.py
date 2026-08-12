from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.incident import (
    Incident as IncidentDB,
)
from app.models.incident import Incident
from app.repositories.incident_repository import (
    IncidentRepository,
)


class PostgresIncidentRepository(
    IncidentRepository
):
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def save(
        self,
        incident: Incident,
    ) -> bool:
        if self.exists(
            incident.incident_id
        ):
            return False

        db_incident = self._to_db_model(
            incident
        )

        self.session.add(
            db_incident
        )

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False

        return True

    def get(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        statement = select(
            IncidentDB
        ).where(
            IncidentDB.incident_id
            == incident_id
        )

        db_incident = self.session.execute(
            statement
        ).scalar_one_or_none()

        if db_incident is None:
            return None

        return self._to_domain_model(
            db_incident
        )

    def update(
        self,
        incident: Incident,
    ) -> bool:
        statement = select(
            IncidentDB
        ).where(
            IncidentDB.incident_id
            == incident.incident_id
        )

        db_incident = self.session.execute(
            statement
        ).scalar_one_or_none()

        if db_incident is None:
            return False

        self._update_db_model(
            db_incident,
            incident,
        )

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False

        return True

    def list_incidents(
        self,
    ) -> List[Incident]:
        statement = (
            select(IncidentDB)
            .order_by(
                IncidentDB.created_at.desc()
            )
        )

        db_incidents = (
            self.session.execute(
                statement
            )
            .scalars()
            .all()
        )

        return [
            self._to_domain_model(
                db_incident
            )
            for db_incident
            in db_incidents
        ]

    def exists(
        self,
        incident_id: str,
    ) -> bool:
        statement = select(
            IncidentDB.id
        ).where(
            IncidentDB.incident_id
            == incident_id
        )

        result = self.session.execute(
            statement
        ).scalar_one_or_none()

        return result is not None

    @staticmethod
    def _to_db_model(
        incident: Incident,
    ) -> IncidentDB:
        return IncidentDB(
            incident_id=incident.incident_id,
            title=incident.title,
            description=incident.description,
            severity=incident.severity.value,
            status=incident.status.value,
            cloud_provider=(
                incident.cloud_provider
            ),
            account_id=incident.account_id,
            region=incident.region,
            source_ip=incident.source_ip,
            user_identity=(
                incident.user_identity
            ),
            correlation_rule_id=(
                incident.correlation_rule_id
            ),
            alert_ids=incident.alert_ids,
            event_ids=incident.event_ids,
            mitre_tactic=(
                incident.mitre_tactic
            ),
            mitre_technique=(
                incident.mitre_technique
            ),
            mitre_technique_id=(
                incident.mitre_technique_id
            ),
            metadata_json=incident.metadata,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            acknowledged_at=(
                incident.acknowledged_at
            ),
            resolved_at=(
                incident.resolved_at
            ),
        )

    @staticmethod
    def _to_domain_model(
        db_incident: IncidentDB,
    ) -> Incident:
        return Incident(
            incident_id=(
                db_incident.incident_id
            ),
            title=db_incident.title,
            description=(
                db_incident.description
            ),
            severity=db_incident.severity,
            status=db_incident.status,
            cloud_provider=(
                db_incident.cloud_provider
            ),
            account_id=db_incident.account_id,
            region=db_incident.region,
            source_ip=db_incident.source_ip,
            user_identity=(
                db_incident.user_identity
            ),
            correlation_rule_id=(
                db_incident.correlation_rule_id
            ),
            alert_ids=(
                db_incident.alert_ids or []
            ),
            event_ids=(
                db_incident.event_ids or []
            ),
            mitre_tactic=(
                db_incident.mitre_tactic
            ),
            mitre_technique=(
                db_incident.mitre_technique
            ),
            mitre_technique_id=(
                db_incident.mitre_technique_id
            ),
            metadata=(
                db_incident.metadata_json
                or {}
            ),
            created_at=(
                db_incident.created_at
            ),
            updated_at=(
                db_incident.updated_at
            ),
            acknowledged_at=(
                db_incident.acknowledged_at
            ),
            resolved_at=(
                db_incident.resolved_at
            ),
        )

    @staticmethod
    def _update_db_model(
        db_incident: IncidentDB,
        incident: Incident,
    ) -> None:
        db_incident.title = (
            incident.title
        )

        db_incident.description = (
            incident.description
        )

        db_incident.severity = (
            incident.severity.value
        )

        db_incident.status = (
            incident.status.value
        )

        db_incident.cloud_provider = (
            incident.cloud_provider
        )

        db_incident.account_id = (
            incident.account_id
        )

        db_incident.region = (
            incident.region
        )

        db_incident.source_ip = (
            incident.source_ip
        )

        db_incident.user_identity = (
            incident.user_identity
        )

        db_incident.correlation_rule_id = (
            incident.correlation_rule_id
        )

        db_incident.alert_ids = (
            incident.alert_ids
        )

        db_incident.event_ids = (
            incident.event_ids
        )

        db_incident.mitre_tactic = (
            incident.mitre_tactic
        )

        db_incident.mitre_technique = (
            incident.mitre_technique
        )

        db_incident.mitre_technique_id = (
            incident.mitre_technique_id
        )

        db_incident.metadata_json = (
            incident.metadata
        )

        db_incident.created_at = (
            incident.created_at
        )

        db_incident.updated_at = (
            incident.updated_at
        )

        db_incident.acknowledged_at = (
            incident.acknowledged_at
        )

        db_incident.resolved_at = (
            incident.resolved_at
        )
