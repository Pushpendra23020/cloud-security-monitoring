from app.models.alert import (
    Alert,
    AlertSeverity,
)
from app.notifications.console import (
    ConsoleNotifier,
)


def build_alert():
    return Alert(
        rule_id="AWS-CONSOLE-001",
        rule_name="Console Test Alert",
        severity=AlertSeverity.HIGH,
        event_id="event-console-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
        resource_id="i-console-test",
    )


def test_console_notifier_success(
    capsys,
):
    alert = build_alert()

    notifier = ConsoleNotifier()

    result = notifier.send(alert)

    assert result is True

    captured = capsys.readouterr()

    assert "SECURITY ALERT" in captured.out
    assert "HIGH" in captured.out
    assert "Console Test Alert" in captured.out
