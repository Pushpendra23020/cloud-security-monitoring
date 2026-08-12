import pytest

from app.models.security_event import SecurityEvent
from app.pipeline.event_validator import (
    InvalidSecurityEvent,
    validate_event,
)


def test_valid_event_passes_validation():
    event = SecurityEvent(
        cloud_provider="aws",
        event_name="ConsoleLogin",
    )

    validated = validate_event(event)

    assert validated.event_name == "ConsoleLogin"


def test_unsupported_cloud_provider_fails():
    event = SecurityEvent(
        cloud_provider="unknown-cloud",
        event_name="TestEvent",
    )

    with pytest.raises(InvalidSecurityEvent):
        validate_event(event)


def test_invalid_severity_fails():
    event = SecurityEvent(
        cloud_provider="aws",
        event_name="ConsoleLogin",
        severity="super-dangerous",
    )

    with pytest.raises(InvalidSecurityEvent):
        validate_event(event)
