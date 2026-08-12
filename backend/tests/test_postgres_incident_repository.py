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


def build_incident() -> Incident:
    unique = str(uuid4())

    return Incident(
        incident_id=(
            f"incident-test-{unique}"
        ),
        title=(
            "Possible AWS Console "
            "Brute Force"
        ),
        description=(
            "Multiple failed AWS "
            "console login attempts."
        ),
        severity="high",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        source_ip="192.0.2.10",
        correlation_rule_id=(
            "AWS-CORR-001"
        ),
        alert_ids=[
            f"alert-{unique}",
        ],
        event_ids=[
            f"event-a-{unique}",
            f"event-b-{unique}",
        ],
        metadata={
            "source": "pytest",
        },
    )


def cleanup_incident(
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


def test_postgres_incident_save_and_get():
    incident = build_incident()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresIncidentRepository(
                    session
                )
            )

            assert repository.save(
                incident
            ) is True

            stored = repository.get(
                incident.incident_id
            )

            assert stored is not None

            assert (
                stored.incident_id
                == incident.incident_id
            )

            assert stored.status == "open"

            assert stored.severity == "high"

            assert (
                stored.correlation_rule_id
                == "AWS-CORR-001"
            )

    finally:
        cleanup_incident(
            incident.incident_id
        )


def test_postgres_incident_update():
    incident = build_incident()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresIncidentRepository(
                    session
                )
            )

            assert repository.save(
                incident
            ) is True

            stored = repository.get(
                incident.incident_id
            )

            assert stored is not None

            stored.description = (
                "Updated incident"
            )

            stored.status = (
                "investigating"
            )

            assert repository.update(
                stored
            ) is True

            updated = repository.get(
                incident.incident_id
            )

            assert updated is not None

            assert (
                updated.description
                == "Updated incident"
            )

            assert (
                updated.status
                == "investigating"
            )

    finally:
        cleanup_incident(
            incident.incident_id
        )


def test_duplicate_incident_not_saved():
    incident = build_incident()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresIncidentRepository(
                    session
                )
            )

            assert repository.save(
                incident
            ) is True

            assert repository.save(
                incident
            ) is False

    finally:
        cleanup_incident(
            incident.incident_id
        )


def test_list_incidents():
    first = build_incident()
    second = build_incident()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresIncidentRepository(
                    session
                )
            )

            assert repository.save(
                first
            ) is True

            assert repository.save(
                second
            ) is True

            incidents = (
                repository.list_incidents()
            )

            ids = {
                incident.incident_id
                for incident in incidents
            }

            assert (
                first.incident_id
                in ids
            )

            assert (
                second.incident_id
                in ids
            )

    finally:
        cleanup_incident(
            first.incident_id
        )

        cleanup_incident(
            second.incident_id
        )
