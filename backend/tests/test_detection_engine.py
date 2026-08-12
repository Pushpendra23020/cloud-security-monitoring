from app.models.security_event import SecurityEvent
from app.rules.engine import DetectionEngine
from app.rules.rule import DetectionRule, RuleCondition


def build_console_login_event() -> SecurityEvent:
    return SecurityEvent(
        event_id="event-123",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        source_ip="192.0.2.10",
        user_identity="test-user",
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


def build_no_mfa_rule() -> DetectionRule:
    return DetectionRule(
        rule_id="AWS-AUTH-001",
        name="Console Login Without MFA",
        description=(
            "Detects AWS console login attempts "
            "performed without MFA."
        ),
        severity="high",
        cloud_provider="aws",
        event_name="ConsoleLogin",
        service="signin",
        conditions=[
            RuleCondition(
                field=(
                    "raw_event."
                    "additionalEventData."
                    "MFAUsed"
                ),
                operator="equals",
                value="No",
            )
        ],
        mitre_tactic="Initial Access",
        mitre_technique="Valid Accounts",
        mitre_technique_id="T1078",
    )


def test_matching_rule_creates_alert():
    event = build_console_login_event()
    rule = build_no_mfa_rule()

    engine = DetectionEngine(
        rules=[rule],
    )

    alerts = engine.evaluate(event)

    assert len(alerts) == 1

    alert = alerts[0]

    assert alert.rule_id == "AWS-AUTH-001"
    assert alert.severity == "high"

    assert alert.event_id == "event-123"
    assert alert.event_name == "ConsoleLogin"

    assert alert.account_id == "123456789012"
    assert alert.region == "us-east-1"

    assert alert.source_ip == "192.0.2.10"
    assert alert.user_identity == "test-user"

    assert alert.mitre_technique_id == "T1078"


def test_non_matching_rule_creates_no_alert():
    event = build_console_login_event()

    rule = DetectionRule(
        rule_id="AWS-IAM-001",
        name="IAM User Created",
        severity="medium",
        event_name="CreateUser",
    )

    engine = DetectionEngine(
        rules=[rule],
    )

    alerts = engine.evaluate(event)

    assert alerts == []


def test_disabled_rule_is_ignored():
    event = build_console_login_event()

    rule = build_no_mfa_rule()
    rule.enabled = False

    engine = DetectionEngine(
        rules=[rule],
    )

    alerts = engine.evaluate(event)

    assert alerts == []


def test_all_conditions_must_match():
    event = build_console_login_event()

    rule = DetectionRule(
        rule_id="AWS-AUTH-002",
        name="Successful Login Without MFA",
        severity="high",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field=(
                    "raw_event."
                    "additionalEventData."
                    "MFAUsed"
                ),
                operator="equals",
                value="No",
            ),
            RuleCondition(
                field=(
                    "raw_event."
                    "responseElements."
                    "ConsoleLogin"
                ),
                operator="equals",
                value="Success",
            ),
        ],
    )

    engine = DetectionEngine(
        rules=[rule],
    )

    alerts = engine.evaluate(event)

    assert alerts == []


def test_multiple_rules_can_match():
    event = build_console_login_event()

    rule_one = build_no_mfa_rule()

    rule_two = DetectionRule(
        rule_id="AWS-AUTH-003",
        name="Failed Console Login",
        severity="medium",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field=(
                    "raw_event."
                    "responseElements."
                    "ConsoleLogin"
                ),
                operator="equals",
                value="Failure",
            )
        ],
    )

    engine = DetectionEngine(
        rules=[
            rule_one,
            rule_two,
        ],
    )

    alerts = engine.evaluate(event)

    assert len(alerts) == 2

    rule_ids = {
        alert.rule_id
        for alert in alerts
    }

    assert rule_ids == {
        "AWS-AUTH-001",
        "AWS-AUTH-003",
    }


def test_add_rule():
    engine = DetectionEngine()

    rule = build_no_mfa_rule()

    engine.add_rule(rule)

    assert len(engine.rules) == 1
    assert engine.rules[0].rule_id == "AWS-AUTH-001"

def test_same_rule_and_event_generate_same_detection_key():
    event = build_console_login_event()
    rule = build_no_mfa_rule()

    engine = DetectionEngine(
        rules=[rule],
    )

    first = engine.evaluate(event)[0]
    second = engine.evaluate(event)[0]

    assert (
        first.detection_key
        == second.detection_key
    )

    assert (
        first.alert_id
        != second.alert_id
    )
