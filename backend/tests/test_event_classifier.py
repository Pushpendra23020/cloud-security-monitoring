from app.models.security_event import SecurityEvent
from app.pipeline.event_classifier import classify_event


def test_failed_console_login_is_medium():
    event = SecurityEvent(
        cloud_provider="aws",
        event_name="ConsoleLogin",
        success=False,
        error_code="FailedAuthentication",
    )

    classified = classify_event(event)

    assert classified.severity == "medium"


def test_successful_console_login_is_info():
    event = SecurityEvent(
        cloud_provider="aws",
        event_name="ConsoleLogin",
        success=True,
    )

    classified = classify_event(event)

    assert classified.severity == "info"


def test_create_access_key_is_high():
    event = SecurityEvent(
        cloud_provider="aws",
        event_name="CreateAccessKey",
        success=True,
    )

    classified = classify_event(event)

    assert classified.severity == "high"


def test_stop_logging_is_critical():
    event = SecurityEvent(
        cloud_provider="aws",
        event_name="StopLogging",
        success=True,
    )

    classified = classify_event(event)

    assert classified.severity == "critical"
