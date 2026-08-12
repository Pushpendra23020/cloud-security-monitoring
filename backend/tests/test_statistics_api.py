from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api.v1.statistics import router
from app.database.models.alert import Alert as AlertDB
from app.database.session import SessionLocal
from app.models.alert import Alert
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)


app = FastAPI()

app.include_router(
    router,
    prefix="/api/v1",
)

client = TestClient(app)


def build_alert(
    *,
    severity: str,
    status: str,
) -> Alert:
    unique = str(uuid4())

    return Alert(
        alert_id=f"stats-alert-{unique}",
        rule_id="AWS-STATS-001",
        rule_name="Statistics Test Alert",
        severity=severity,
        status=status,
        event_id=f"stats-event-{unique}",
        event_name="TestEvent",
        detection_key=f"stats-detection-{unique}",
        cloud_provider="aws",
    )


def save_alert(
    alert: Alert,
) -> None:
    with SessionLocal() as session:
        repository = (
            PostgresAlertRepository(
                session
            )
        )

        assert repository.save(
            alert
        ) is True


def cleanup() -> None:
    with SessionLocal() as session:
        session.execute(
            delete(AlertDB).where(
                AlertDB.rule_id
                == "AWS-STATS-001"
            )
        )

        session.commit()


def test_statistics_endpoint():
    alerts = [
        build_alert(
            severity="critical",
            status="open",
        ),
        build_alert(
            severity="high",
            status="open",
        ),
        build_alert(
            severity="medium",
            status="resolved",
        ),
        build_alert(
            severity="low",
            status="false_positive",
        ),
    ]

    try:
        for alert in alerts:
            save_alert(alert)

        response = client.get(
            "/api/v1/statistics"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] >= 4
        assert data["open"] >= 2
        assert data["resolved"] >= 1
        assert data["false_positive"] >= 1

        assert data["critical"] >= 1
        assert data["high"] >= 1
        assert data["medium"] >= 1
        assert data["low"] >= 1

    finally:
        cleanup()
