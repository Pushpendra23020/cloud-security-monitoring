from pathlib import Path

from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
)
from app.services.alert_service import AlertService
from app.storage.json_alert_store import JsonAlertStore


def build_alert(
    alert_id: str,
    *,
    source_ip: str = "192.0.2.10",
    resource_id: str = "i-1234567890",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        rule_id="AWS-TEST-001",
        rule_name="Suspicious AWS Activity",
        severity=AlertSeverity.HIGH,
        event_id=f"event-{alert_id}",
        event_name="ConsoleLogin",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        source_ip=source_ip,
        user_identity="test-user",
        resource_type="ec2",
        resource_id=resource_id,
    )


def test_fingerprint_is_stable(tmp_path):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    first = build_alert("alert-001")
    second = build_alert("alert-002")

    first_fingerprint = (
        service.generate_fingerprint(first)
    )

    second_fingerprint = (
        service.generate_fingerprint(second)
    )

    assert first_fingerprint
    assert first_fingerprint == second_fingerprint


def test_same_security_condition_is_deduplicated(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    first = build_alert("alert-001")
    second = build_alert("alert-002")

    assert service.save_alert(first) is True
    assert service.save_alert(second) is True

    alerts = service.get_all_alerts()

    assert len(alerts) == 1

    stored = alerts[0]

    assert stored.alert_id == "alert-001"
    assert stored.occurrence_count == 2
    assert stored.first_seen_at <= stored.last_seen_at


def test_same_alert_id_is_rejected(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    alert = build_alert("alert-001")

    assert service.save_alert(alert) is True
    assert service.save_alert(alert) is False

    alerts = service.get_all_alerts()

    assert len(alerts) == 1
    assert alerts[0].occurrence_count == 1


def test_different_source_ip_creates_new_alert(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    first = build_alert(
        "alert-001",
        source_ip="192.0.2.10",
    )

    second = build_alert(
        "alert-002",
        source_ip="203.0.113.25",
    )

    assert service.save_alert(first) is True
    assert service.save_alert(second) is True

    alerts = service.get_all_alerts()

    assert len(alerts) == 2


def test_different_resource_creates_new_alert(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    first = build_alert(
        "alert-001",
        resource_id="i-1111111111",
    )

    second = build_alert(
        "alert-002",
        resource_id="i-2222222222",
    )

    assert service.save_alert(first) is True
    assert service.save_alert(second) is True

    alerts = service.get_all_alerts()

    assert len(alerts) == 2


def test_resolved_alert_allows_new_alert(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    first = build_alert("alert-001")

    assert service.save_alert(first) is True

    stored = service.get_alert(
        "alert-001"
    )

    assert stored is not None

    stored.status = AlertStatus.RESOLVED

    assert service.update_alert(
        stored
    ) is True

    second = build_alert("alert-002")

    assert service.save_alert(second) is True

    alerts = service.get_all_alerts()

    assert len(alerts) == 2


def test_last_seen_changes_on_duplicate(
    tmp_path,
):
    store = JsonAlertStore(
        str(tmp_path / "alerts.jsonl")
    )
    service = AlertService(store)

    first = build_alert("alert-001")

    assert service.save_alert(first) is True

    before = service.get_alert(
        "alert-001"
    )

    assert before is not None

    previous_last_seen = (
        before.last_seen_at
    )

    second = build_alert("alert-002")

    assert service.save_alert(second) is True

    after = service.get_alert(
        "alert-001"
    )

    assert after is not None

    assert after.occurrence_count == 2
    assert after.last_seen_at >= previous_last_seen
