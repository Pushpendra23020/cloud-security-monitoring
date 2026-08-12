from math import ceil

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from app.schemas.alert import (
    AlertListResponse,
    AlertResponse,
    AlertStatusUpdateResponse,
)
from app.models.alert import AlertSeverity, AlertStatus
from app.services.alert_service import AlertService
from app.services.status_transition import InvalidStatusTransition


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


def get_alert_repository(
    db: Session = Depends(get_db),
) -> PostgresAlertRepository:
    return PostgresAlertRepository(db)


def get_alert_service(
    repository: PostgresAlertRepository = Depends(
        get_alert_repository
    ),
) -> AlertService:
    return AlertService(repository)


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List security alerts",
)
def list_alerts(
    severity: AlertSeverity | None = Query(
        default=None,
    ),
    alert_status: AlertStatus | None = Query(
        default=None,
        alias="status",
    ),
    cloud_provider: str | None = Query(
        default=None,
    ),
    account_id: str | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="created_at",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    repository: PostgresAlertRepository = Depends(
        get_alert_repository
    ),
) -> AlertListResponse:
    alerts, total = repository.list_alerts(
        severity=(
            severity.value
            if severity is not None
            else None
        ),
        status=(
            alert_status.value
            if alert_status is not None
            else None
        ),
        cloud_provider=cloud_provider,
        account_id=account_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    items = [
        AlertResponse.model_validate(alert)
        for alert in alerts
    ]

    return AlertListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get security alert",
)
def get_alert(
    alert_id: str,
    repository: PostgresAlertRepository = Depends(
        get_alert_repository
    ),
) -> AlertResponse:
    alert = repository.get(alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return AlertResponse.model_validate(alert)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertStatusUpdateResponse,
    summary="Acknowledge security alert",
)
def acknowledge_alert(
    alert_id: str,
    service: AlertService = Depends(
        get_alert_service
    ),
) -> AlertStatusUpdateResponse:
    try:
        alert = service.acknowledge_alert(
            alert_id
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return AlertStatusUpdateResponse(
        alert_id=alert.alert_id,
        status=alert.status,
        updated_at=alert.updated_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
    )


@router.post(
    "/{alert_id}/investigate",
    response_model=AlertStatusUpdateResponse,
    summary="Mark security alert as investigating",
)
def investigate_alert(
    alert_id: str,
    service: AlertService = Depends(
        get_alert_service
    ),
) -> AlertStatusUpdateResponse:
    try:
        alert = service.investigate_alert(
            alert_id
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return AlertStatusUpdateResponse(
        alert_id=alert.alert_id,
        status=alert.status,
        updated_at=alert.updated_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
    )


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertStatusUpdateResponse,
    summary="Resolve security alert",
)
def resolve_alert(
    alert_id: str,
    service: AlertService = Depends(
        get_alert_service
    ),
) -> AlertStatusUpdateResponse:
    try:
        alert = service.resolve_alert(
            alert_id
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return AlertStatusUpdateResponse(
        alert_id=alert.alert_id,
        status=alert.status,
        updated_at=alert.updated_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
    )


@router.post(
    "/{alert_id}/false-positive",
    response_model=AlertStatusUpdateResponse,
    summary="Mark security alert as false positive",
)
def mark_false_positive(
    alert_id: str,
    service: AlertService = Depends(
        get_alert_service
    ),
) -> AlertStatusUpdateResponse:
    try:
        alert = service.mark_false_positive(
            alert_id
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return AlertStatusUpdateResponse(
        alert_id=alert.alert_id,
        status=alert.status,
        updated_at=alert.updated_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
    )
