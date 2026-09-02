import hmac
from datetime import datetime
from typing import Any, Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.dependencies import CurrentOrganizationId
from app.dependencies import require_roles
from app.repositories.event_queue_repository import EventQueueRepository


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


class CloudTrailEventRequest(BaseModel):
    event: dict[str, Any]


class CloudTrailEventResponse(BaseModel):
    processed: int
    saved: int
    duplicates: int
    failed: int
    errors: list[dict[str, Any]]


class EventQueueStatusResponse(BaseModel):
    queued: int = 0
    processing: int = 0
    retry: int = 0
    completed: int = 0
    dead_letter: int = 0
    oldest_pending_age_seconds: int = 0
    healthy: bool = True


class DeadLetterEventResponse(BaseModel):
    id: int
    event_id: str
    source: str
    attempts: int
    max_attempts: int
    last_error: str | None
    received_at: datetime
    archived_at: datetime | None
    archive_uri: str | None


class DeadLetterPageResponse(BaseModel):
    items: list[DeadLetterEventResponse]
    total: int
    page: int
    page_size: int
    pages: int


class EventReplayResponse(BaseModel):
    requeued: bool


def verify_ingestion_api_key(
    x_api_key: Annotated[
        str | None,
        Header(alias="X-API-Key"),
    ] = None,
) -> None:
    configured_key = (
        settings.EVENT_INGEST_API_KEY
    )

    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event ingestion is not configured",
        )

    if (
        x_api_key is None
        or not hmac.compare_digest(
            x_api_key,
            configured_key,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion API key",
        )


@router.post(
    "/cloudtrail",
    response_model=CloudTrailEventResponse,
    dependencies=[
        Depends(verify_ingestion_api_key),
    ],
)
def ingest_cloudtrail_event(
    request: CloudTrailEventRequest,
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
):
    return EventQueueRepository(db, organization_id).enqueue_batch(
        [request.event],
        source="cloudtrail",
        max_attempts=settings.EVENT_QUEUE_MAX_ATTEMPTS,
    )


@router.get("/queue", response_model=EventQueueStatusResponse)
def queue_status(
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
) -> EventQueueStatusResponse:
    return EventQueueStatusResponse(
        **EventQueueRepository(db, organization_id).health(
            alert_age_seconds=settings.EVENT_QUEUE_ALERT_AGE_SECONDS
        )
    )


@router.get("/queue/dead-letters", response_model=DeadLetterPageResponse)
def list_dead_letter_events(
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> DeadLetterPageResponse:
    records, total = EventQueueRepository(
        db,
        organization_id,
    ).list_dead_letters(page=page, page_size=page_size)
    return DeadLetterPageResponse(
        items=[
            DeadLetterEventResponse(
                id=record.id,
                event_id=record.event_id,
                source=record.source,
                attempts=record.attempts,
                max_attempts=record.max_attempts,
                last_error=record.last_error,
                received_at=record.received_at,
                archived_at=record.archived_at,
                archive_uri=record.archive_uri,
            )
            for record in records
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "/queue/{record_id}/replay",
    response_model=EventReplayResponse,
    dependencies=[Depends(require_roles("admin", "analyst"))],
)
def replay_dead_letter_event(
    record_id: int,
    organization_id: CurrentOrganizationId,
    db: Session = Depends(get_db),
) -> EventReplayResponse:
    requeued = EventQueueRepository(
        db,
        organization_id,
    ).replay_dead_letter(record_id)
    if not requeued:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dead-letter event not found.",
        )
    return EventReplayResponse(requeued=True)
