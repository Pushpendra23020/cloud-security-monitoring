from datetime import timezone

from app.models.incident import (
    Incident,
    IncidentStatus,
)


def build_incident() -> Incident:
    return Incident(
        title=(
            "Possible AWS "
            "Account Compromise"
        ),
        description=(
            "Multiple suspicious AWS "
            "authentication events."
        ),
        severity="high",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        source_ip="192.0.2.10",
        correlation_rule_id=(
            "AWS-CORR-001"
        ),
        alert_ids=[
            "alert-001",
        ],
        event_ids=[
            "event-001",
            "event-002",
        ],
    )


def test_incident_creation():
    incident = build_incident()

    assert (
        incident.incident_id.startswith(
            "incident-"
        )
    )

    assert incident.status == "open"

    assert incident.severity == "high"

    assert (
        incident.cloud_provider
        == "aws"
    )

    assert (
        incident.created_at.tzinfo
        == timezone.utc
    )


def test_incident_assignment_validation():
    incident = build_incident()

    incident.status = (
        "investigating"
    )

    assert incident.status == (
        IncidentStatus.INVESTIGATING
    )


def test_incident_severity_assignment_validation():
    incident = build_incident()

    incident.severity = "critical"

    assert (
        incident.severity
        == "critical"
    )
