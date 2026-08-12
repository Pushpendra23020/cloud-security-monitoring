import pytest

from app.models.alert import AlertStatus
from app.services.status_transition import (
    InvalidStatusTransition,
    validate_transition,
)


TRANSITIONS = {
    AlertStatus.OPEN: {
        AlertStatus.ACKNOWLEDGED,
        AlertStatus.INVESTIGATING,
        AlertStatus.RESOLVED,
        AlertStatus.FALSE_POSITIVE,
    },
    AlertStatus.ACKNOWLEDGED: {
        AlertStatus.INVESTIGATING,
        AlertStatus.RESOLVED,
        AlertStatus.FALSE_POSITIVE,
    },
    AlertStatus.INVESTIGATING: {
        AlertStatus.RESOLVED,
        AlertStatus.FALSE_POSITIVE,
    },
    AlertStatus.RESOLVED: set(),
    AlertStatus.FALSE_POSITIVE: set(),
}


def test_valid_transition():
    validate_transition(
        AlertStatus.OPEN,
        AlertStatus.INVESTIGATING,
        TRANSITIONS,
    )


def test_invalid_transition():
    with pytest.raises(
        InvalidStatusTransition
    ):
        validate_transition(
            AlertStatus.RESOLVED,
            AlertStatus.INVESTIGATING,
            TRANSITIONS,
        )


def test_same_status_is_allowed():
    validate_transition(
        AlertStatus.OPEN,
        AlertStatus.OPEN,
        TRANSITIONS,
    )
