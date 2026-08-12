from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from sqlalchemy import delete, select

from app.database.models.alert import (
    Alert as AlertDB,
)
from app.database.models.incident import (
    Incident as IncidentDB,
)
from app.database.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.pipeline.detection_pipeline import (
    DetectionPipeline,
)
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from app.repositories.postgres_incident_repository import (
    PostgresIncidentRepository,
)
from app.services.alert_service import (
    AlertService,
)
from app.services.incident_service import (
    IncidentService,
)


def test_correlation_alert_creates_incident():
    unique = str(uuid4())

    source_ip = "203.0.113.77"

    base_time = datetime(
        2026,
        8,
        12,
        15,
        0,
        tzinfo=timezone.utc,
    )

    event_ids = [
        f"incident-event-{unique}-{i}"
        for i in range(5)
    ]

    created_incident_ids = []

    try:
        with SessionLocal() as session:
            alert_repository = (
                PostgresAlertRepository(
                    session
                )
            )

            incident_repository = (
                PostgresIncidentRepository(
                    session
                )
            )

            alert_service = AlertService(
                alert_repository
            )

            incident_service = (
                IncidentService(
                    incident_repository
                )
            )

            pipeline = DetectionPipeline(
                alert_service=alert_service,
                incident_service=(
                    incident_service
                ),
            )

            generated_alerts = []

            for i in range(5):
                event = SecurityEvent(
                    event_id=event_ids[i],
                    timestamp=(
                        base_time
                        + timedelta(
                            minutes=i
                        )
                    ),
                    cloud_provider="aws",
                    account_id=(
                        "123456789012"
                    ),
                    region="us-east-1",
                    service="signin",
                    event_name=(
                        "ConsoleLogin"
                    ),
                    source_ip=source_ip,
                    success=False,
                    raw_event={
                        "responseElements": {
                            "ConsoleLogin": (
                                "Failure"
                            ),
                        },
                        "additionalEventData": {
                            "MFAUsed": "No",
                        },
                    },
                )

                generated_alerts.extend(
                    pipeline.process(
                        event
                    )
                )

            correlation_alerts = [
                alert
                for alert
                in generated_alerts
                if alert.rule_id
                == "AWS-CORR-001"
            ]

            assert (
                len(correlation_alerts)
                == 1
            )

            correlation_alert = (
                correlation_alerts[0]
            )

            # Incident ID should be assigned
            # back onto the alert.
            assert (
                correlation_alert.incident_id
                is not None
            )

            created_incident_ids.append(
                correlation_alert.incident_id
            )

            # Verify alert persisted with
            # incident_id.
            stored_alert = (
                alert_service.get_alert(
                    correlation_alert.alert_id
                )
            )

            assert stored_alert is not None

            assert (
                stored_alert.incident_id
                == correlation_alert.incident_id
            )

            # Verify incident exists.
            incident = (
                incident_service.get_incident(
                    correlation_alert.incident_id
                )
            )

            assert incident is not None

            assert (
                incident.correlation_rule_id
                == "AWS-CORR-001"
            )

            assert (
                incident.status
                == "open"
            )

            assert (
                correlation_alert.alert_id
                in incident.alert_ids
            )

            assert (
                len(incident.event_ids)
                == 5
            )

            assert set(
                incident.event_ids
            ) == set(
                event_ids
            )

            assert (
                incident.metadata[
                    "matched_event_count"
                ]
                == 5
            )

    finally:
        with SessionLocal() as session:
            # Remove all alerts produced
            # from these test events.
            session.execute(
                delete(AlertDB).where(
                    AlertDB.event_id.in_(
                        event_ids
                    )
                )
            )

            if created_incident_ids:
                session.execute(
                    delete(
                        IncidentDB
                    ).where(
                        IncidentDB.incident_id.in_(
                            created_incident_ids
                        )
                    )
                )

            session.commit()
