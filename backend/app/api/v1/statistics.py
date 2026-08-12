from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from app.schemas.alert import AlertStatisticsResponse
from app.services.alert_service import AlertService


router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)


def get_alert_service(
    db: Session = Depends(get_db),
) -> AlertService:
    repository = PostgresAlertRepository(
        db
    )

    return AlertService(
        repository
    )


@router.get(
    "",
    response_model=AlertStatisticsResponse,
    summary="Get alert statistics",
)
def get_statistics(
    service: AlertService = Depends(
        get_alert_service
    ),
) -> AlertStatisticsResponse:
    stats = service.get_statistics()

    return AlertStatisticsResponse(
        **stats
    )
