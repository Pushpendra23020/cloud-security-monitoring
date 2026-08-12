from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api.v1.incidents import router
from app.database.models.incident import (
    Incident as IncidentDB,
)
from app.database.session import SessionLocal
from app.models.incident import Incident
from app.repositories.postgres_incident_repository import (
    PostgresIncidentRepository,
)


app = FastAPI()

app.include_router(
    router,
    prefix="/api/v1",
)

client = TestClient(app)


def build_incident() -> Incident:
    unique = str(uuid4())

    return Incident(
        incident_id=f"incident-api-{unique}",
        title="API Incident Test",
        severity="high",
        cloud_provider="aws",
        correlation_rule_id="AWS-CORR-001",
        alert_ids=[],
        event_ids=[],
    )


def save_incident(
    incident: Incident,
) -> None:
    with SessionLocal() as session:
        repository = (
            PostgresIncidentRepository(
                session
            )
        )

        assert repository.save(
            incident
        ) is True


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


def test_list_incidents_api():
    incident = build_incident()

    try:
        save_incident(incident)

        response = client.get(
            "/api/v1/incidents"
        )

        assert response.status_code == 200

        data = response.json()

        ids = {
            item["incident_id"]
            for item in data["items"]
        }

        assert incident.incident_id in ids

    finally:
        cleanup(
            incident.incident_id
        )


def test_get_incident_api():
    incident = build_incident()

    try:
        save_incident(incident)

        response = client.get(
            f"/api/v1/incidents/{incident.incident_id}"
        )

        assert response.status_code == 200

        data = response.json()

        assert (
            data["incident_id"]
            == incident.incident_id
        )

        assert data["status"] == "open"

    finally:
        cleanup(
            incident.incident_id
        )


def test_incident_lifecycle_api():
    incident = build_incident()

    try:
        save_incident(incident)

        response = client.post(
            f"/api/v1/incidents/{incident.incident_id}/acknowledge"
        )

        assert response.status_code == 200
        assert (
            response.json()["status"]
            == "acknowledged"
        )

        response = client.post(
            f"/api/v1/incidents/{incident.incident_id}/investigate"
        )

        assert response.status_code == 200
        assert (
            response.json()["status"]
            == "investigating"
        )

        response = client.post(
            f"/api/v1/incidents/{incident.incident_id}/resolve"
        )

        assert response.status_code == 200
        assert (
            response.json()["status"]
            == "resolved"
        )

    finally:
        cleanup(
            incident.incident_id
        )


def test_missing_incident_returns_404():
    response = client.get(
        "/api/v1/incidents/does-not-exist"
    )

    assert response.status_code == 404


def test_resolved_incident_cannot_be_investigated():
    incident = build_incident()

    try:
        save_incident(incident)

        response = client.post(
            f"/api/v1/incidents/"
            f"{incident.incident_id}/resolve"
        )

        assert response.status_code == 200

        response = client.post(
            f"/api/v1/incidents/"
            f"{incident.incident_id}/investigate"
        )

        assert response.status_code == 409

        assert (
            "Cannot transition"
            in response.json()["detail"]
        )

    finally:
        cleanup(
            incident.incident_id
        )
