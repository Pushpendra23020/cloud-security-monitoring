from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.storage.json_alert_store import JsonAlertStore


def build_alert(
    alert_id: str = "alert-001",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        rule_id="AWS-TEST-001",
        rule_name="Repository Test Rule",
        severity="high",
        event_id="event-001",
        event_name="TestEvent",
        cloud_provider="aws",
        detection_key=f"detection-{alert_id}",
    )


def test_json_alert_store_implements_repository(tmp_path):
    repository = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    assert isinstance(
        repository,
        AlertRepository,
    )


def test_repository_save_and_get(tmp_path):
    repository = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    alert = build_alert()

    assert repository.save(alert) is True

    stored = repository.get(
        alert.alert_id
    )

    assert stored is not None
    assert stored.alert_id == alert.alert_id


def test_repository_update(tmp_path):
    repository = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    alert = build_alert()

    repository.save(alert)

    alert.description = "Updated description"

    assert repository.update(alert) is True

    stored = repository.get(
        alert.alert_id
    )

    assert stored is not None
    assert stored.description == "Updated description"


def test_repository_prevents_duplicate_detection(tmp_path):
    repository = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )

    first = build_alert("alert-001")
    second = build_alert("alert-002")

    second.detection_key = first.detection_key

    assert repository.save(first) is True
    assert repository.save(second) is False
