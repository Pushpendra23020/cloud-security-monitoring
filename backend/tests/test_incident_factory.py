from app.models.alert import Alert
from app.services.incident_factory import (
    IncidentFactory,
)


def test_incident_created_from_correlation_alert():
    alert = Alert(
        alert_id="alert-corr-001",
        rule_id="AWS-CORR-001",
        rule_name=(
            "Possible AWS Console Brute Force"
        ),
        description=(
            "Multiple failed AWS console "
            "login attempts."
        ),
        severity="high",
        event_id="event-005",
        event_name="ConsoleLogin",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        source_ip="192.0.2.10",
        mitre_tactic="Credential Access",
        mitre_technique="Brute Force",
        mitre_technique_id="T1110",
        metadata={
            "threshold": 5,
            "matched_event_count": 5,
            "matched_event_ids": [
                "event-001",
                "event-002",
                "event-003",
                "event-004",
                "event-005",
            ],
            "group_by": "source_ip",
            "group_value": "192.0.2.10",
        },
    )

    incident = (
        IncidentFactory
        .from_correlation_alert(
            alert
        )
    )

    assert (
        incident.correlation_rule_id
        == "AWS-CORR-001"
    )

    assert incident.severity == "high"

    assert (
        incident.source_ip
        == "192.0.2.10"
    )

    assert len(
        incident.event_ids
    ) == 5

    assert (
        incident.metadata[
            "matched_event_count"
        ]
        == 5
    )

    assert (
        incident.metadata[
            "source_alert_id"
        ]
        == "alert-corr-001"
    )
