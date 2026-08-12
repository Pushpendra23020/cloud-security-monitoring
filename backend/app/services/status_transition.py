from enum import Enum


class InvalidStatusTransition(ValueError):
    pass


def validate_transition(
    current_status: Enum,
    target_status: Enum,
    allowed_transitions: dict,
) -> None:
    if current_status == target_status:
        return

    allowed = allowed_transitions.get(
        current_status,
        set(),
    )

    if target_status not in allowed:
        raise InvalidStatusTransition(
            f"Cannot transition from "
            f"{current_status.value} to "
            f"{target_status.value}"
        )
