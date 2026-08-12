from uuid import uuid4

from sqlalchemy import delete

from app.database.models.incident import (
    Incident as IncidentDB,
)
from app.database.session import SessionLocal
from app.models.incident import Incident
from app.repositories.postgres_incident_repository import (
    PostgresIncidentRepository,
)
from app.services.incident_service import (
    IncidentService,
)


def build_incident() -> Incident:
    unique = str(uuid4())

    return Incident(
        incident_id=(
            f"incident-service-{unique}"
        ),
        title="Incident Service Test",
        severity="high",
        cloud_provider="aws",
        correlation_rule_id=(
            "AWS-CORR-001"
        ),
        alert_ids=[],
        event_ids=[],
    )


def cleanup(
    incident_id: str,
) -> None:
    with SessionLocal() as session:
        session.execute(
            delete(IncidentDB).where(
                IncidentDB.incident_id
                == incident_id
            )
        )

        session.commit()


def test_incident_service_lifecycle():
    incident = build_incident()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresIncidentRepository(
                    session
                )
            )

            service = IncidentService(
                repository
            )

            assert service.save_incident(
                incident
            ) is True

            acknowledged = (
                service.acknowledge_incident(
                    incident.incident_id
                )
            )

            assert acknowledged is not None
            assert (
                acknowledged.status
                == "acknowledged"
            )

            assert (
                acknowledged.acknowledged_at
                is not None
            )

            investigating = (
                service.investigate_incident(
                    incident.incident_id
                )
            )

            assert investigating is not None
            assert (
                investigating.status
                == "investigating"
            )

            resolved = (
                service.resolve_incident(
                    incident.incident_id
                )
            )

            assert resolved is not None
            assert (
                resolved.status
                == "resolved"
            )

            assert (
                resolved.resolved_at
                is not None
            )

            persisted = (
                service.get_incident(
                    incident.incident_id
                )
            )

            assert persisted is not None

            assert (
                persisted.status
                == "resolved"
            )

    finally:
        cleanup(
            incident.incident_id
        )


def test_incident_service_missing_returns_none():
    with SessionLocal() as session:
        repository = (
            PostgresIncidentRepository(
                session
            )
        )

        service = IncidentService(
            repository
        )

        assert (
            service.get_incident(
                "does-not-exist"
            )
            is None
        )

        assert (
            service.resolve_incident(
                "does-not-exist"
            )
            is None
        )
