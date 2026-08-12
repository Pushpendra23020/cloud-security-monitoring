from uuid import uuid4

from sqlalchemy import delete, select

from app.database.models.incident import (
    Incident as IncidentDB,
)
from app.database.session import SessionLocal


def test_incident_database_model():
    incident_id = (
        f"incident-db-{uuid4()}"
    )

    try:
        with SessionLocal() as session:
            incident = IncidentDB(
                incident_id=incident_id,
                title="Database Incident Test",
                description=(
                    "Testing incident persistence."
                ),
                severity="high",
                status="open",
                cloud_provider="aws",
                account_id="123456789012",
                region="us-east-1",
                source_ip="192.0.2.10",
                correlation_rule_id=(
                    "AWS-CORR-001"
                ),
                alert_ids=[
                    "alert-001",
                ],
                event_ids=[
                    "event-001",
                    "event-002",
                ],
                metadata_json={
                    "source": "pytest",
                },
            )

            session.add(incident)
            session.commit()

            stored = session.execute(
                select(IncidentDB).where(
                    IncidentDB.incident_id
                    == incident_id
                )
            ).scalar_one()

            assert (
                stored.incident_id
                == incident_id
            )

            assert stored.severity == "high"
            assert stored.status == "open"

            assert stored.alert_ids == [
                "alert-001"
            ]

            assert stored.event_ids == [
                "event-001",
                "event-002",
            ]

            assert stored.metadata_json == {
                "source": "pytest"
            }

    finally:
        with SessionLocal() as session:
            session.execute(
                delete(IncidentDB).where(
                    IncidentDB.incident_id
                    == incident_id
                )
            )

            session.commit()
