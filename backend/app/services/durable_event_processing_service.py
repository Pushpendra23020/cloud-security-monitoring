from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.security_event import SecurityEventRecord
from app.models.security_event import SecurityEvent
from app.notifications.factory import NotificationDispatcherFactory
from app.pipeline.cloudtrail_pipeline import CloudTrailIngestionPipeline
from app.pipeline.detection_pipeline import DetectionPipeline
from app.repositories.postgres_alert_repository import PostgresAlertRepository
from app.repositories.postgres_incident_repository import PostgresIncidentRepository
from app.services.alert_service import AlertService
from app.services.incident_service import IncidentService


class DurableEventProcessingService:
    @staticmethod
    def process(db: Session, record: SecurityEventRecord) -> None:
        organization_id = record.organization_id
        alert_service = AlertService(
            repository=PostgresAlertRepository(db, organization_id),
            dispatcher=NotificationDispatcherFactory.build(
                settings,
                organization_id=organization_id,
            ),
        )
        incident_service = IncidentService(
            PostgresIncidentRepository(db, organization_id)
        )
        pipeline = CloudTrailIngestionPipeline(
            organization_id=organization_id,
            persist_events=False,
            detection_pipeline=DetectionPipeline(
                alert_service=alert_service,
                incident_service=incident_service,
                organization_id=organization_id,
            ),
        )
        pipeline.process_normalized(
            SecurityEvent.model_validate(record.normalized_event),
            persist=False,
        )
