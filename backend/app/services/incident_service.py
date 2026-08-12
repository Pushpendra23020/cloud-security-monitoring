from datetime import datetime, timezone
from typing import List, Optional

from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.repositories.incident_repository import (
    IncidentRepository,
)
from app.services.status_transition import (
    validate_transition,
)


class IncidentService:
    INCIDENT_TRANSITIONS = {
        IncidentStatus.OPEN: {
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING,
            IncidentStatus.RESOLVED,
            IncidentStatus.FALSE_POSITIVE,
        },
        IncidentStatus.ACKNOWLEDGED: {
            IncidentStatus.INVESTIGATING,
            IncidentStatus.RESOLVED,
            IncidentStatus.FALSE_POSITIVE,
        },
        IncidentStatus.INVESTIGATING: {
            IncidentStatus.RESOLVED,
            IncidentStatus.FALSE_POSITIVE,
        },
        IncidentStatus.RESOLVED: set(),
        IncidentStatus.FALSE_POSITIVE: set(),
    }

    def __init__(
        self,
        repository: IncidentRepository,
    ):
        self.repository = repository

    def save_incident(
        self,
        incident: Incident,
    ) -> bool:
        return self.repository.save(
            incident
        )

    def get_incident(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        return self.repository.get(
            incident_id
        )

    def list_incidents(
        self,
    ) -> List[Incident]:
        return (
            self.repository.list_incidents()
        )

    def acknowledge_incident(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        incident = self.get_incident(
            incident_id
        )

        if incident is None:
            return None

        validate_transition(
            incident.status,
            IncidentStatus.ACKNOWLEDGED,
            self.INCIDENT_TRANSITIONS,
        )

        now = datetime.now(
            timezone.utc
        )

        incident.status = (
            IncidentStatus.ACKNOWLEDGED
        )
        incident.acknowledged_at = now
        incident.updated_at = now

        self.repository.update(
            incident
        )

        return incident

    def investigate_incident(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        incident = self.get_incident(
            incident_id
        )

        if incident is None:
            return None

        validate_transition(
            incident.status,
            IncidentStatus.INVESTIGATING,
            self.INCIDENT_TRANSITIONS,
        )

        incident.status = (
            IncidentStatus.INVESTIGATING
        )
        incident.updated_at = datetime.now(
            timezone.utc
        )

        self.repository.update(
            incident
        )

        return incident

    def resolve_incident(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        incident = self.get_incident(
            incident_id
        )

        if incident is None:
            return None

        validate_transition(
            incident.status,
            IncidentStatus.RESOLVED,
            self.INCIDENT_TRANSITIONS,
        )

        now = datetime.now(
            timezone.utc
        )

        incident.status = (
            IncidentStatus.RESOLVED
        )
        incident.resolved_at = now
        incident.updated_at = now

        self.repository.update(
            incident
        )

        return incident

    def mark_false_positive(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        incident = self.get_incident(
            incident_id
        )

        if incident is None:
            return None

        validate_transition(
            incident.status,
            IncidentStatus.FALSE_POSITIVE,
            self.INCIDENT_TRANSITIONS,
        )

        now = datetime.now(
            timezone.utc
        )

        incident.status = (
            IncidentStatus.FALSE_POSITIVE
        )
        incident.resolved_at = now
        incident.updated_at = now

        self.repository.update(
            incident
        )

        return incident
