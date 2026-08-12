from app.models.security_event import SecurityEvent
from app.pipeline.detection_pipeline import DetectionPipeline
from datetime import datetime, timedelta, timezone

from app.services.alert_service import AlertService
from app.storage.json_alert_store import JsonAlertStore

def test_detection_pipeline_detects_console_login_without_mfa():
    event = SecurityEvent(
        event_id="event-001",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        success=False,
        raw_event={
            "responseElements": {
                "ConsoleLogin": "Failure",
            },
            "additionalEventData": {
                "MFAUsed": "No",
            },
        },
    )

    pipeline = DetectionPipeline()

    alerts = pipeline.process(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }


    assert "AWS-AUTH-002" in rule_ids
    assert "AWS-AUTH-003" in rule_ids
    assert "AWS-AUTH-001" not in rule_ids

def test_detection_pipeline_ignores_normal_event():
    event = SecurityEvent(
        event_id="event-002",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="ec2",
        event_name="DescribeInstances",
        raw_event={},
    )

    pipeline = DetectionPipeline()

    alerts = pipeline.process(event)

    assert alerts == []
def test_detection_pipeline_generates_brute_force_alert(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    alert_service = AlertService(store)

    pipeline = DetectionPipeline(
        alert_service=alert_service
    )

    base_time = datetime(
        2026,
        8,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    generated_alerts = []

    for i in range(5):
        event = SecurityEvent(
            event_id=f"failed-login-{i}",
            timestamp=(
                base_time
                + timedelta(minutes=i)
            ),
            cloud_provider="aws",
            account_id="123456789012",
            region="us-east-1",
            service="signin",
            event_name="ConsoleLogin",
            source_ip="192.0.2.10",
            success=False,
            raw_event={
                "responseElements": {
                    "ConsoleLogin": "Failure",
                },
                "additionalEventData": {
                    "MFAUsed": "No",
                },
            },
        )

        generated_alerts.extend(
            pipeline.process(event)
        )

    correlation_alerts = [
        alert
        for alert in generated_alerts
        if alert.rule_id == "AWS-CORR-001"
    ]

    assert len(correlation_alerts) == 1

    alert = correlation_alerts[0]

    assert alert.severity == "high"
    assert (
        alert.metadata[
            "matched_event_count"
        ]
        == 5
    )


def test_correlation_alert_is_persisted(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    alert_service = AlertService(store)

    pipeline = DetectionPipeline(
        alert_service=alert_service
    )

    base_time = datetime(
        2026,
        8,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    for i in range(5):
        event = SecurityEvent(
            event_id=f"event-{i}",
            timestamp=(
                base_time
                + timedelta(minutes=i)
            ),
            cloud_provider="aws",
            service="signin",
            event_name="ConsoleLogin",
            source_ip="203.0.113.10",
            success=False,
            raw_event={
                "responseElements": {
                    "ConsoleLogin": "Failure",
                },
                "additionalEventData": {
                    "MFAUsed": "No",
                },
            },
        )

        pipeline.process(event)

    saved_alerts = (
        alert_service.get_all_alerts()
    )

    correlation_alerts = [
        alert
        for alert in saved_alerts
        if alert.rule_id == "AWS-CORR-001"
    ]

    assert len(correlation_alerts) == 1
