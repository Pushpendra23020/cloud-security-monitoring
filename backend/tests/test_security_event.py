from app.models.security_event import SecurityEvent


def test_security_event_creation():
    event = SecurityEvent(
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        source_ip="192.168.1.10",
        user_identity="admin-user",
        success=True,
    )

    assert event.cloud_provider == "aws"
    assert event.event_name == "ConsoleLogin"
    assert event.success is True
    assert event.event_id is not None
    assert event.timestamp is not None
