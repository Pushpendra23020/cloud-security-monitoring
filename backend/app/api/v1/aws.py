from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.aws import AWSIdentityResponse
from app.schemas.aws_collection import (
    EC2CollectionRequest,
    EC2CollectionResponse,
)
from app.services.aws_ingestion_service import AWSIngestionService
from app.services.aws_service import AWSService


router = APIRouter(
    prefix="/aws",
    tags=["AWS"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/identity",
    response_model=AWSIdentityResponse,
)
def verify_aws_identity():
    return AWSService.verify_connection()


@router.post(
    "/ec2/collect",
    response_model=EC2CollectionResponse,
)
def collect_ec2(
    request: EC2CollectionRequest,
    db: DatabaseSession,
):

    try:
        return AWSIngestionService.ingest_ec2_instances(
            db=db,
            cloud_account_id=request.cloud_account_id,
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
