from app.rules.rule import DetectionRule, RuleCondition


def test_rule_condition_creation():
    condition = RuleCondition(
        field="event_name",
        operator="equals",
        value="ConsoleLogin",
    )

    assert condition.field == "event_name"
    assert condition.operator == "equals"
    assert condition.value == "ConsoleLogin"


def test_detection_rule_creation():
    rule = DetectionRule(
        rule_id="AWS-AUTH-001",
        name="Console Login Without MFA",
        description="Detects AWS console login without MFA.",
        severity="high",
        event_name="ConsoleLogin",
        service="signin",
        conditions=[
            RuleCondition(
                field="raw_event.additionalEventData.MFAUsed",
                operator="equals",
                value="No",
            )
        ],
    )

    assert rule.rule_id == "AWS-AUTH-001"
    assert rule.name == "Console Login Without MFA"

    assert rule.cloud_provider == "aws"
    assert rule.event_name == "ConsoleLogin"
    assert rule.service == "signin"

    assert rule.severity == "high"
    assert rule.enabled is True

    assert len(rule.conditions) == 1

    assert (
        rule.conditions[0].field
        == "raw_event.additionalEventData.MFAUsed"
    )


def test_detection_rule_defaults():
    rule = DetectionRule(
        rule_id="AWS-TEST-001",
        name="Test Rule",
        severity="low",
    )

    assert rule.enabled is True
    assert rule.cloud_provider == "aws"
    assert rule.conditions == []
    assert rule.metadata == {}


def test_detection_rule_supports_mitre_metadata():
    rule = DetectionRule(
        rule_id="AWS-IAM-001",
        name="Root Account Activity",
        severity="critical",
        mitre_tactic="Privilege Escalation",
        mitre_technique="Valid Accounts",
        mitre_technique_id="T1078",
    )

    assert rule.mitre_tactic == "Privilege Escalation"
    assert rule.mitre_technique == "Valid Accounts"
    assert rule.mitre_technique_id == "T1078"

