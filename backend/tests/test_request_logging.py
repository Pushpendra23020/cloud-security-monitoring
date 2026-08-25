from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_request_id_is_generated():
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_request_id_is_preserved():
    request_id = "security-test-request-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_health_endpoint_remains_available():
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "Cloud Security Monitoring"


def test_readiness_endpoint_exists():
    response = client.get("/ready")

    assert response.status_code in (200, 503)
