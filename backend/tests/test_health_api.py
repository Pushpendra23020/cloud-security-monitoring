from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready_endpoint_when_database_available():
    mock_connection = MagicMock()

    with patch("app.main.engine.connect") as connect:
        connect.return_value.__enter__.return_value = mock_connection

        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }


def test_ready_endpoint_when_database_unavailable():
    from sqlalchemy.exc import OperationalError

    with patch(
        "app.main.engine.connect",
        side_effect=OperationalError(
            "SELECT 1",
            {},
            Exception("database unavailable"),
        ),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
