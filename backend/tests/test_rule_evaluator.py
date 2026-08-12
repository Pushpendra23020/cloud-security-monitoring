import pytest

from app.models.security_event import SecurityEvent
from app.rules.evaluator import ConditionEvaluator
from app.rules.rule import RuleCondition


def build_event() -> SecurityEvent:
    return SecurityEvent(
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
            "userIdentity": {
                "type": "IAMUser",
            },
        },
    )


def test_get_top_level_field():
    event = build_event()

    value = ConditionEvaluator.get_field_value(
        event,
        "event_name",
    )

    assert value == "ConsoleLogin"


def test_get_nested_raw_event_field():
    event = build_event()

    value = ConditionEvaluator.get_field_value(
        event,
        "raw_event.additionalEventData.MFAUsed",
    )

    assert value == "No"


def test_missing_field_returns_none():
    event = build_event()

    value = ConditionEvaluator.get_field_value(
        event,
        "raw_event.does.not.exist",
    )

    assert value is None


def test_equals_operator():
    event = build_event()

    condition = RuleCondition(
        field="event_name",
        operator="equals",
        value="ConsoleLogin",
    )

    assert ConditionEvaluator.evaluate(
        event,
        condition,
    ) is True


def test_not_equals_operator():
    event = build_event()

    condition = RuleCondition(
        field="region",
        operator="not_equals",
        value="eu-west-1",
    )

    assert ConditionEvaluator.evaluate(
        event,
        condition,
    ) is True


def test_contains_operator():
    event = build_event()

    condition = RuleCondition(
        field="event_name",
        operator="contains",
        value="Login",
    )

    assert ConditionEvaluator.evaluate(
        event,
        condition,
    ) is True


def test_in_operator():
    event = build_event()

    condition = RuleCondition(
        field="region",
        operator="in",
        value=[
            "us-east-1",
            "us-west-2",
        ],
    )

    assert ConditionEvaluator.evaluate(
        event,
        condition,
    ) is True


def test_exists_operator_true():
    event = build_event()

    condition = RuleCondition(
        field="raw_event.userIdentity.type",
        operator="exists",
        value=True,
    )

    assert ConditionEvaluator.evaluate(
        event,
        condition,
    ) is True


def test_exists_operator_false():
    event = build_event()

    condition = RuleCondition(
        field="raw_event.errorCode",
        operator="exists",
        value=False,
    )

    assert ConditionEvaluator.evaluate(
        event,
        condition,
    ) is True


def test_unsupported_operator_raises_error():
    event = build_event()

    condition = RuleCondition(
        field="event_name",
        operator="unknown_operator",
        value="ConsoleLogin",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported rule operator",
    ):
        ConditionEvaluator.evaluate(
            event,
            condition,
        )
