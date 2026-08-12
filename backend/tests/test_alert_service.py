from app.models.alert import Alert
from app.services.alert_service import AlertService
from app.storage.json_alert_store import JsonAlertStore


def build_alert(
    alert_id: str,
) -> Alert:
    return Alert(
        alert_id=alert_id,
        rule_id="AWS-AUTH-001",
        rule_name="Console Login Without MFA",
        severity="high",
        event_id="event-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
    )


def test_save_single_alert(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    result = service.save_alert(
        build_alert("alert-001")
    )

    assert result is True

    alerts = service.get_all_alerts()

    assert len(alerts) == 1


def test_save_multiple_alerts(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    saved = service.save_alerts(
        [
            build_alert("alert-001"),
            build_alert("alert-002"),
        ]
    )

    assert saved == 2

    alerts = service.get_all_alerts()

    assert len(alerts) == 2


def test_duplicate_alert_is_not_saved_twice(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    alert = build_alert("alert-001")

    first = service.save_alert(alert)
    second = service.save_alert(alert)

    assert first is True
    assert second is False

    assert len(
        service.get_all_alerts()
    ) == 1
