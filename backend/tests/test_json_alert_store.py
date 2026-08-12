from app.models.alert import Alert
from app.storage.json_alert_store import JsonAlertStore


def build_alert(
    alert_id: str = "alert-001",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        rule_id="AWS-AUTH-001",
        rule_name="Console Login Without MFA",
        severity="high",
        event_id="event-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
    )


def test_save_alert(tmp_path):
    file_path = tmp_path / "alerts.jsonl"

    store = JsonAlertStore(
        str(file_path)
    )

    alert = build_alert()

    saved = store.save(alert)

    assert saved is True
    assert file_path.exists()


def test_load_all_alerts(tmp_path):
    file_path = tmp_path / "alerts.jsonl"

    store = JsonAlertStore(
        str(file_path)
    )

    store.save(
        build_alert("alert-001")
    )

    store.save(
        build_alert("alert-002")
    )

    alerts = store.load_all()

    assert len(alerts) == 2

    alert_ids = {
        alert.alert_id
        for alert in alerts
    }

    assert alert_ids == {
        "alert-001",
        "alert-002",
    }


def test_duplicate_alert_not_saved(tmp_path):
    file_path = tmp_path / "alerts.jsonl"

    store = JsonAlertStore(
        str(file_path)
    )

    alert = build_alert()

    first_save = store.save(alert)
    second_save = store.save(alert)

    assert first_save is True
    assert second_save is False

    alerts = store.load_all()

    assert len(alerts) == 1


def test_exists_returns_true_for_saved_alert(
    tmp_path,
):
    file_path = tmp_path / "alerts.jsonl"

    store = JsonAlertStore(
        str(file_path)
    )

    alert = build_alert()

    store.save(alert)

    assert store.exists(
        alert.alert_id
    ) is True


def test_exists_returns_false_for_unknown_alert(
    tmp_path,
):
    file_path = tmp_path / "alerts.jsonl"

    store = JsonAlertStore(
        str(file_path)
    )

    assert store.exists(
        "missing-alert"
    ) is False
def test_same_detection_not_saved_twice(
    tmp_path,
):
    file_path = tmp_path / "alerts.jsonl"

    store = JsonAlertStore(
        str(file_path)
    )

    first = Alert(
        alert_id="alert-001",
        detection_key="same-detection",
        rule_id="AWS-AUTH-001",
        rule_name="Console Login Without MFA",
        severity="high",
        event_id="event-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
    )

    second = Alert(
        alert_id="alert-002",
        detection_key="same-detection",
        rule_id="AWS-AUTH-001",
        rule_name="Console Login Without MFA",
        severity="high",
        event_id="event-001",
        event_name="ConsoleLogin",
        cloud_provider="aws",
    )

    assert store.save(first) is True
    assert store.save(second) is False

    assert len(
        store.load_all()
    ) == 1
