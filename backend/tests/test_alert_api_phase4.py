from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api.v1.alerts import router
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


def build_alert() -> Alert:
    unique = str(uuid4())

    return Alert(
        alert_id=f"alert-api-{unique}",
        rule_id="AWS-API-TEST-001",
        rule_name="API Test Alert",
        description="Phase 4 API integration test.",
        severity="high",
        event_id=f"event-api-{unique}",
        event_name="ConsoleLogin",
        detection_key=f"detection-api-{unique}",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        source_ip="192.0.2.50",
        user_identity="api-test-user",
        metadata={
            "source": "api-test",
        },
    )


def save_alert(
    alert: Alert,
) -> None:
    with SessionLocal() as session:
        repository = PostgresAlertRepository(
            session
        )

        assert repository.save(alert) is True


def cleanup_alert(
    alert_id: str,
) -> None:
    with SessionLocal() as session:
        session.execute(
            delete(AlertDB).where(
                AlertDB.alert_id == alert_id
            )
        )

        session.commit()


def test_list_alerts():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.get(
            "/api/v1/alerts"
        )

        assert response.status_code == 200

        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

        alert_ids = {
            item["alert_id"]
            for item in data["items"]
        }

        assert alert.alert_id in alert_ids

    finally:
        cleanup_alert(alert.alert_id)


def test_get_alert_by_id():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.get(
            f"/api/v1/alerts/{alert.alert_id}"
        )

        assert response.status_code == 200

        data = response.json()

        assert (
            data["alert_id"]
            == alert.alert_id
        )

        assert (
            data["rule_id"]
            == "AWS-API-TEST-001"
        )

        assert data["severity"] == "high"
        assert data["status"] == "open"

        assert (
            data["cloud_provider"]
            == "aws"
        )

    finally:
        cleanup_alert(alert.alert_id)


def test_get_missing_alert_returns_404():
    response = client.get(
        "/api/v1/alerts/does-not-exist"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Alert not found"
    }
def test_filter_alerts_by_severity():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.get(
            "/api/v1/alerts",
            params={
                "severity": "high",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert all(
            item["severity"] == "high"
            for item in data["items"]
        )

    finally:
        cleanup_alert(alert.alert_id)


def test_filter_alerts_by_status():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.get(
            "/api/v1/alerts",
            params={
                "status": "open",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert all(
            item["status"] == "open"
            for item in data["items"]
        )

    finally:
        cleanup_alert(alert.alert_id)


def test_alert_pagination():
    first = build_alert()
    second = build_alert()

    try:
        save_alert(first)
        save_alert(second)

        response = client.get(
            "/api/v1/alerts",
            params={
                "page": 1,
                "page_size": 1,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 1

        assert len(
            data["items"]
        ) <= 1

        assert data["total"] >= 2
        assert data["pages"] >= 2

    finally:
        cleanup_alert(first.alert_id)
        cleanup_alert(second.alert_id)


def test_invalid_page_is_rejected():
    response = client.get(
        "/api/v1/alerts",
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_invalid_page_size_is_rejected():
    response = client.get(
        "/api/v1/alerts",
        params={
            "page_size": 1000,
        },
    )

    assert response.status_code == 422


def test_invalid_sort_order_is_rejected():
    response = client.get(
        "/api/v1/alerts",
        params={
            "sort_order": "random",
        },
    )
    assert response.status_code == 422

def test_acknowledge_alert_api():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.post(
            f"/api/v1/alerts/{alert.alert_id}/acknowledge"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["alert_id"] == alert.alert_id
        assert data["status"] == "acknowledged"
        assert data["acknowledged_at"] is not None

    finally:
        cleanup_alert(alert.alert_id)


def test_investigate_alert_api():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.post(
            f"/api/v1/alerts/{alert.alert_id}/investigate"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "investigating"

    finally:
        cleanup_alert(alert.alert_id)


def test_resolve_alert_api():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.post(
            f"/api/v1/alerts/{alert.alert_id}/resolve"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None

    finally:
        cleanup_alert(alert.alert_id)


def test_false_positive_alert_api():
    alert = build_alert()

    try:
        save_alert(alert)

        response = client.post(
            f"/api/v1/alerts/{alert.alert_id}/false-positive"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "false_positive"
        assert data["resolved_at"] is not None

    finally:
        cleanup_alert(alert.alert_id)


def test_lifecycle_missing_alert_returns_404():
    endpoints = [
        "acknowledge",
        "investigate",
        "resolve",
        "false-positive",
    ]

    for endpoint in endpoints:
        response = client.post(
            f"/api/v1/alerts/does-not-exist/{endpoint}"
        )

        assert response.status_code == 404

        assert response.json() == {
            "detail": "Alert not found"
        }


def test_invalid_severity_filter_returns_422():
    response = client.get(
        "/api/v1/alerts",
        params={
            "severity": "not-a-severity"
        },
    )

    assert response.status_code == 422


def test_invalid_status_filter_returns_422():
    response = client.get(
        "/api/v1/alerts",
        params={
            "status": "not-a-status"
        },
    )

    assert response.status_code == 422
