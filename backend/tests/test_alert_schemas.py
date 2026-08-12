from datetime import datetime, timezone

from app.models.alert import Alert
from app.schemas.alert import (
    AlertListResponse,
    AlertResponse,
    AlertStatisticsResponse,
    AlertStatusUpdateResponse,
)


def build_alert() -> Alert:
    return Alert(
        alert_id="alert-schema-001",
        rule_id="AWS-AUTH-001",
        rule_name="Console Login Without MFA",
        description=(
            "AWS console login occurred "
            "without MFA."
        ),
        severity="high",
        event_id="event-schema-001",
        event_name="ConsoleLogin",
        detection_key="detection-schema-001",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        source_ip="192.0.2.10",
        user_identity="test-user",
        metadata={
            "source": "schema-test",
        },
    )


def test_alert_response_from_domain_model():
    alert = build_alert()

    response = AlertResponse.model_validate(
        alert
    )

    assert response.alert_id == alert.alert_id
    assert response.rule_id == alert.rule_id
    assert response.severity == "high"
    assert response.status == "open"

    assert response.cloud_provider == "aws"

    assert response.metadata == {
        "source": "schema-test",
    }


def test_alert_response_serializes_to_json():
    alert = build_alert()

    response = AlertResponse.model_validate(
        alert
    )

    data = response.model_dump(
        mode="json"
    )

    assert data["severity"] == "high"
    assert data["status"] == "open"

    assert isinstance(
        data["created_at"],
        str,
    )


def test_alert_list_response():
    alert = build_alert()

    item = AlertResponse.model_validate(
        alert
    )

    response = AlertListResponse(
        items=[item],
        total=1,
        page=1,
        page_size=50,
        pages=1,
    )

    assert response.total == 1
    assert response.page == 1
    assert response.page_size == 50
    assert response.pages == 1

    assert len(response.items) == 1


def test_alert_status_update_response():
    now = datetime.now(
        timezone.utc
    )

    response = AlertStatusUpdateResponse(
        alert_id="alert-001",
        status="acknowledged",
        updated_at=now,
        acknowledged_at=now,
    )

    assert response.status == "acknowledged"

    assert (
        response.acknowledged_at
        is not None
    )


def test_alert_statistics_response():
    response = AlertStatisticsResponse(
        total=10,
        open=4,
        acknowledged=1,
        investigating=2,
        resolved=2,
        false_positive=1,
        info=0,
        low=1,
        medium=3,
        high=4,
        critical=2,
    )

    assert response.total == 10
    assert response.open == 4
    assert response.critical == 2
