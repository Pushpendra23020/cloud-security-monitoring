import hmac
from typing import Any, Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from pydantic import BaseModel

from app.config import settings
from app.pipeline.cloudtrail_pipeline import (
    CloudTrailIngestionPipeline,
)


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
):
    pipeline = CloudTrailIngestionPipeline()

    return pipeline.process_batch(
        [request.event]
    )
