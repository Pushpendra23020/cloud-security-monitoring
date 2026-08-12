from datetime import timezone

from app.models.alert import Alert


def test_alert_creation():
    alert = Alert(
        rule_id="AWS-AUTH-001",
        rule_name="Console Login Without MFA",
        description="AWS console login occurred without MFA.",
        severity="high",
        event_id="event-123",
        event_name="ConsoleLogin",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        source_ip="192.0.2.10",
        user_identity="test-user",
    )

    assert alert.rule_id == "AWS-AUTH-001"
    assert alert.rule_name == "Console Login Without MFA"
    assert alert.severity == "high"

    assert alert.event_id == "event-123"
    assert alert.event_name == "ConsoleLogin"

    assert alert.cloud_provider == "aws"
    assert alert.account_id == "123456789012"
    assert alert.region == "us-east-1"

    assert alert.status == "open"

    assert alert.alert_id is not None
    assert len(alert.alert_id) > 0

    assert alert.created_at.tzinfo == timezone.utc


def test_alert_supports_mitre_metadata():
    alert = Alert(
        rule_id="AWS-IAM-001",
        rule_name="Root Account Activity",
        severity="critical",
        event_id="event-456",
        event_name="CreateUser",
        cloud_provider="aws",
        mitre_tactic="Privilege Escalation",
        mitre_technique="Valid Accounts",
        mitre_technique_id="T1078",
    )

    assert alert.mitre_tactic == "Privilege Escalation"
    assert alert.mitre_technique == "Valid Accounts"
    assert alert.mitre_technique_id == "T1078"


def test_alert_metadata_defaults_to_empty_dict():
    alert = Alert(
        rule_id="AWS-TEST-001",
        rule_name="Test Rule",
        severity="low",
        event_id="event-789",
        event_name="TestEvent",
        cloud_provider="aws",
    )

    assert alert.metadata == {}


def test_alert_status_defaults_to_open():
    alert = Alert(
        rule_id="AWS-TEST-002",
        rule_name="Another Test Rule",
        severity="medium",
        event_id="event-999",
        event_name="AnotherEvent",
        cloud_provider="aws",
    )

    assert alert.status == "open"


def test_alert_severity_is_validated():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Alert(
            rule_id="TEST-001",
            rule_name="Invalid Severity",
            severity="super-dangerous",
            event_id="event-001",
            event_name="TestEvent",
            cloud_provider="aws",
        )


def test_alert_status_is_validated():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Alert(
            rule_id="TEST-002",
            rule_name="Invalid Status",
            severity="low",
            status="random-status",
            event_id="event-002",
            event_name="TestEvent",
            cloud_provider="aws",
        )
