from app.models.security_event import SecurityEvent
from app.rules.aws_rules import AWS_RULES
from app.rules.engine import DetectionEngine


def test_aws_rules_loaded():
    assert len(AWS_RULES) >= 8


def test_rule_ids_are_unique():
    rule_ids = [
        rule.rule_id
        for rule in AWS_RULES
    ]

    assert len(rule_ids) == len(set(rule_ids))


def test_failed_console_login_without_mfa_detected():
    event = SecurityEvent(
        event_id="event-console-1",
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

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert "AWS-AUTH-002" in rule_ids
    assert "AWS-AUTH-003" in rule_ids

    assert "AWS-AUTH-001" not in rule_ids


def test_successful_console_login_without_mfa_detected():
    event = SecurityEvent(
        event_id="event-console-success",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        success=True,
        raw_event={
            "responseElements": {
                "ConsoleLogin": "Success",
            },
            "additionalEventData": {
                "MFAUsed": "No",
            },
        },
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert "AWS-AUTH-001" in rule_ids

    assert "AWS-AUTH-002" not in rule_ids
    assert "AWS-AUTH-003" not in rule_ids


def test_root_console_login_detected():
    event = SecurityEvent(
        event_id="event-root-console",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        success=True,
        raw_event={
            "userIdentity": {
                "type": "Root",
            },
            "responseElements": {
                "ConsoleLogin": "Success",
            },
            "additionalEventData": {
                "MFAUsed": "Yes",
            },
        },
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert "AWS-ROOT-001" in rule_ids


def test_root_read_only_activity_not_critical():
    event = SecurityEvent(
        event_id="event-root-read",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="iam",
        event_name="ListUsers",
        raw_event={
            "userIdentity": {
                "type": "Root",
            }
        },
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    critical_alerts = [
        alert
        for alert in alerts
        if alert.severity == "critical"
    ]

    assert critical_alerts == []


def test_root_sensitive_iam_activity_detected():
    event = SecurityEvent(
        event_id="event-root-delete-user",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="iam",
        event_name="DeleteUser",
        raw_event={
            "userIdentity": {
                "type": "Root",
            }
        },
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert "AWS-ROOT-002" in rule_ids


def test_iam_user_creation_detected():
    event = SecurityEvent(
        event_id="event-create-user",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="iam",
        event_name="CreateUser",
        raw_event={
            "userIdentity": {
                "type": "IAMUser",
            }
        },
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert "AWS-IAM-001" in rule_ids


def test_cloudtrail_stop_logging_detected():
    event = SecurityEvent(
        event_id="event-trail-1",
        cloud_provider="aws",
        service="cloudtrail",
        event_name="StopLogging",
        raw_event={},
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert "AWS-TRAIL-001" in rule_ids


def test_normal_event_does_not_match():
    event = SecurityEvent(
        event_id="event-normal-1",
        cloud_provider="aws",
        service="ec2",
        event_name="DescribeInstances",
        raw_event={},
    )

    engine = DetectionEngine(AWS_RULES)

    alerts = engine.evaluate(event)

    assert alerts == []
