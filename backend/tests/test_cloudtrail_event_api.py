import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)

TEST_API_KEY = "test-cloudtrail-ingestion-key"


def auth_headers():
    return {
        "X-API-Key": TEST_API_KEY,
    }


def build_event():
    return {
        "eventVersion": "1.08",
        "userIdentity": {
            "type": "IAMUser",
            "principalId": "AIDATESTUSER",
            "arn": (
                "arn:aws:iam::123456789012:"
                "user/test-user"
            ),
            "accountId": "123456789012",
            "userName": "test-user",
        },
        "eventTime": (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "198.51.100.88",
        "eventType": "AwsConsoleSignIn",
        "eventID": str(uuid.uuid4()),
        "responseElements": {
            "ConsoleLogin": "Failure",
        },
        "additionalEventData": {
            "MFAUsed": "No",
        },
    }


def setup_module():
    settings.EVENT_INGEST_API_KEY = TEST_API_KEY


def teardown_module():
    settings.EVENT_INGEST_API_KEY = None


def test_cloudtrail_event_ingestion_endpoint():
    response = client.post(
        "/api/v1/events/cloudtrail",
        json={"event": build_event()},
        headers=auth_headers(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["processed"] == 1
    assert data["saved"] == 1
    assert data["duplicates"] == 0
    assert data["failed"] == 0


def test_cloudtrail_event_duplicate():
    event = build_event()

    first = client.post(
        "/api/v1/events/cloudtrail",
        json={"event": event},
        headers=auth_headers(),
    )

    second = client.post(
        "/api/v1/events/cloudtrail",
        json={"event": event},
        headers=auth_headers(),
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert second.json()["saved"] == 0
    assert second.json()["duplicates"] == 1


def test_cloudtrail_event_requires_event_object():
    response = client.post(
        "/api/v1/events/cloudtrail",
        json={},
        headers=auth_headers(),
    )

    assert response.status_code == 422


def test_cloudtrail_event_rejects_missing_api_key():
    response = client.post(
        "/api/v1/events/cloudtrail",
        json={"event": build_event()},
    )

    assert response.status_code == 401


def test_cloudtrail_event_rejects_invalid_api_key():
    response = client.post(
        "/api/v1/events/cloudtrail",
        json={"event": build_event()},
        headers={
            "X-API-Key": "wrong-key",
        },
    )

    assert response.status_code == 401
