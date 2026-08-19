from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.alert import (
    Alert,
    AlertSeverity,
)
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)


client = TestClient(app)


def create_alert() -> Alert:
    suffix = str(uuid4())

    alert = Alert(
        alert_id=f"alert-api-{suffix}",
        rule_id="AWS-NOTIFY-API-001",
        rule_name="Notification API Test",
        severity=AlertSeverity.HIGH,
        event_id=f"event-api-{suffix}",
        event_name="ConsoleLogin",
        detection_key=f"detection-api-{suffix}",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        user_identity=f"api-user-{suffix}",
    )

    with SessionLocal() as session:
        repository = (
            PostgresAlertRepository(
                session
            )
        )

        assert repository.save(
            alert
        ) is True

    return alert


def test_api_suppress_alert():
    alert = create_alert()

    until = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    response = client.post(
        f"/api/v1/alerts/{alert.alert_id}/suppress",
        json={
            "suppressed_until": (
                until.isoformat()
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["notification_status"]
        == "suppressed"
    )

    assert data["suppressed_until"] is not None


def test_api_unsuppress_alert():
    alert = create_alert()

    until = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    suppress_response = client.post(
        f"/api/v1/alerts/{alert.alert_id}/suppress",
        json={
            "suppressed_until": (
                until.isoformat()
            )
        },
    )

    assert suppress_response.status_code == 200

    response = client.post(
        f"/api/v1/alerts/{alert.alert_id}/unsuppress"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["notification_status"]
        == "pending"
    )

    assert data["suppressed_until"] is None


def test_api_suppress_missing_alert():
    response = client.post(
        "/api/v1/alerts/missing-alert/suppress",
        json={
            "suppressed_until": (
                datetime.now(timezone.utc)
                + timedelta(minutes=10)
            ).isoformat()
        },
    )

    assert response.status_code == 404


def test_api_suppress_rejects_past_time():
    alert = create_alert()

    response = client.post(
        f"/api/v1/alerts/{alert.alert_id}/suppress",
        json={
            "suppressed_until": (
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ).isoformat()
        },
    )

    assert response.status_code == 422


def test_api_alert_response_exposes_notification_state():
    alert = create_alert()

    response = client.get(
        f"/api/v1/alerts/{alert.alert_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert "notification_status" in data
    assert "last_notified_at" in data
    assert "suppressed_until" in data
