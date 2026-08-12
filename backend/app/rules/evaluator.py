from typing import Any

from app.models.security_event import SecurityEvent
from app.rules.rule import RuleCondition


class ConditionEvaluator:
    @staticmethod
    def get_field_value(
        event: SecurityEvent,
        field_path: str,
    ) -> Any:
        """
        Resolve dotted field paths from a SecurityEvent.

        Example:
        raw_event.additionalEventData.MFAUsed
        """

        parts = field_path.split(".")

        current: Any = event

        for part in parts:
            if current is None:
                return None

            if isinstance(current, dict):
                current = current.get(part)
                continue

            current = getattr(current, part, None)

        return current

    @classmethod
    def evaluate(
        cls,
        event: SecurityEvent,
        condition: RuleCondition,
    ) -> bool:
        actual_value = cls.get_field_value(
            event,
            condition.field,
        )

        operator = condition.operator
        expected_value = condition.value

        if operator == "equals":
            return actual_value == expected_value

        if operator == "not_equals":
            return actual_value != expected_value

        if operator == "contains":
            if actual_value is None:
                return False

            try:
                return expected_value in actual_value
            except TypeError:
                return False

        if operator == "in":
            if expected_value is None:
                return False

            try:
                return actual_value in expected_value
            except TypeError:
                return False

        if operator == "exists":
            expected_exists = bool(expected_value)

            if expected_exists:
                return actual_value is not None

            return actual_value is None

        raise ValueError(
            f"Unsupported rule operator: {operator}"
        )
