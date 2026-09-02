from sqlalchemy import select

from app.config import settings
from app.database.models.organization import Organization
from app.database.session import SessionLocal, set_tenant_context
from app.repositories.event_queue_repository import EventQueueRepository
from app.utils.metrics import EVENT_QUEUE_DEPTH, EVENT_QUEUE_OLDEST_PENDING_SECONDS


QUEUE_STATES = ("queued", "processing", "retry", "completed", "dead_letter")


def refresh_event_queue_metrics() -> None:
    EVENT_QUEUE_DEPTH.clear()
    EVENT_QUEUE_OLDEST_PENDING_SECONDS.clear()
    with SessionLocal() as discovery_db:
        organization_ids = list(
            discovery_db.scalars(
                select(Organization.id).where(Organization.is_active.is_(True))
            )
        )
    for organization_id in organization_ids:
        with SessionLocal() as db:
            set_tenant_context(db, organization_id)
            health = EventQueueRepository(db, organization_id).health(
                alert_age_seconds=settings.EVENT_QUEUE_ALERT_AGE_SECONDS
            )
        for state in QUEUE_STATES:
            EVENT_QUEUE_DEPTH.labels(
                organization_id=str(organization_id),
                status=state,
            ).set(health.get(state, 0))
        EVENT_QUEUE_OLDEST_PENDING_SECONDS.labels(
            organization_id=str(organization_id)
        ).set(health["oldest_pending_age_seconds"])
