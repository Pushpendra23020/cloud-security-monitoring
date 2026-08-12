from uuid import uuid4

from sqlalchemy import delete

from app.database.models.alert import Alert as AlertDB
from app.database.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.pipeline.detection_pipeline import DetectionPipeline
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from app.services.alert_service import AlertService


def cleanup_event_alerts(
    event_id: str,
) -> None:
    with SessionLocal() as session:
        session.execute(
            delete(AlertDB).where(
                AlertDB.event_id == event_id
            )
        )

        session.commit()


def test_detection_pipeline_persists_alert_to_postgres():
    unique = str(uuid4())

    event_id = f"phase4-event-{unique}"

    event = SecurityEvent(
        event_id=event_id,
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        event_name="ConsoleLogin",
        source_ip="192.0.2.50",
        success=False,
        raw_event={
            "responseElements": {
                "ConsoleLogin": "Failure",
            },
            "additionalEventData": {
                "MFAUsed": "No",
            },
        },
    )

    try:
        with SessionLocal() as session:
            repository = (
                PostgresAlertRepository(
                    session
                )
            )

            alert_service = AlertService(
                repository
            )

            pipeline = DetectionPipeline(
                alert_service=alert_service
            )

            alerts = pipeline.process(
                event
            )

            assert len(alerts) > 0

            generated_ids = {
                alert.alert_id
                for alert in alerts
            }

            persisted_alerts = (
                repository.load_all()
            )

            persisted_ids = {
                alert.alert_id
                for alert in persisted_alerts
            }

            assert generated_ids.issubset(
                persisted_ids
            )

            event_alerts = [
                alert
                for alert in persisted_alerts
                if alert.event_id == event_id
            ]

            assert len(event_alerts) > 0

            rule_ids = {
                alert.rule_id
                for alert in event_alerts
            }

            assert "AWS-AUTH-002" in rule_ids
            assert "AWS-AUTH-003" in rule_ids

    finally:
        cleanup_event_alerts(
            event_id
        )
