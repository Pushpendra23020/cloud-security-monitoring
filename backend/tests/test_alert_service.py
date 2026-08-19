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

    first = build_alert("alert-001")

    second = build_alert("alert-002")
    second.source_ip = "203.0.113.25"

    saved = service.save_alerts(
        [
            first,
            second,
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


def test_get_alert_by_id(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    service.save_alert(
        build_alert("alert-001")
    )

    alert = service.get_alert("alert-001")

    assert alert is not None
    assert alert.alert_id == "alert-001"


def test_get_missing_alert_returns_none(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    alert = service.get_alert("does-not-exist")

    assert alert is None


def test_acknowledge_alert(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    service.save_alert(
        build_alert("alert-001")
    )

    alert = service.acknowledge_alert(
        "alert-001"
    )

    assert alert is not None
    assert alert.status == "acknowledged"
    assert alert.acknowledged_at is not None

    stored = service.get_alert("alert-001")

    assert stored is not None
    assert stored.status == "acknowledged"


def test_investigate_alert(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    service.save_alert(
        build_alert("alert-001")
    )

    alert = service.investigate_alert(
        "alert-001"
    )

    assert alert is not None
    assert alert.status == "investigating"


def test_resolve_alert(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    service.save_alert(
        build_alert("alert-001")
    )

    alert = service.resolve_alert(
        "alert-001"
    )

    assert alert is not None
    assert alert.status == "resolved"
    assert alert.resolved_at is not None


def test_mark_alert_false_positive(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    service = AlertService(store)

    service.save_alert(
        build_alert("alert-001")
    )

    alert = service.mark_false_positive(
        "alert-001"
    )

    assert alert is not None
    assert alert.status == "false_positive"
    assert alert.resolved_at is not None
