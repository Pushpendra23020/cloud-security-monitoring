from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)
from app.repositories.postgres_incident_repository import (
    PostgresIncidentRepository,
)
from app.schemas.alert import AlertResponse
from app.schemas.incident import (
    IncidentAlertsResponse,
    IncidentListResponse,
    IncidentResponse,
    IncidentStatusUpdateResponse,
)
from app.services.incident_service import (
    IncidentService,
)
from app.services.status_transition import (
    InvalidStatusTransition,
)


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


def get_incident_service(
    db: Session = Depends(get_db),
) -> IncidentService:
    repository = PostgresIncidentRepository(
        db
    )

    return IncidentService(
        repository
    )


def get_alert_repository(
    db: Session = Depends(get_db),
) -> PostgresAlertRepository:
    return PostgresAlertRepository(
        db
    )


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List security incidents",
)
def list_incidents(
    service: IncidentService = Depends(
        get_incident_service
    ),
) -> IncidentListResponse:
    incidents = service.list_incidents()

    items = [
        IncidentResponse.model_validate(
            incident
        )
        for incident in incidents
    ]

    return IncidentListResponse(
        items=items,
        total=len(items),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get security incident",
)
def get_incident(
    incident_id: str,
    service: IncidentService = Depends(
        get_incident_service
    ),
) -> IncidentResponse:
    incident = service.get_incident(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return IncidentResponse.model_validate(
        incident
    )


@router.get(
    "/{incident_id}/alerts",
    response_model=IncidentAlertsResponse,
    summary="List alerts linked to an incident",
)
def get_incident_alerts(
    incident_id: str,
    service: IncidentService = Depends(
        get_incident_service
    ),
    alert_repository: PostgresAlertRepository = Depends(
        get_alert_repository
    ),
) -> IncidentAlertsResponse:
    incident = service.get_incident(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    alerts = (
        alert_repository
        .get_by_incident_id(
            incident_id
        )
    )

    items = [
        AlertResponse.model_validate(
            alert
        )
        for alert in alerts
    ]

    return IncidentAlertsResponse(
        incident_id=incident_id,
        items=items,
        total=len(items),
    )


@router.post(
    "/{incident_id}/acknowledge",
    response_model=IncidentStatusUpdateResponse,
    summary="Acknowledge incident",
)
def acknowledge_incident(
    incident_id: str,
    service: IncidentService = Depends(
        get_incident_service
    ),
) -> IncidentStatusUpdateResponse:
    try:
        incident = (
            service.acknowledge_incident(
                incident_id
            )
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return IncidentStatusUpdateResponse(
        incident_id=incident.incident_id,
        status=incident.status,
        updated_at=incident.updated_at,
        acknowledged_at=(
            incident.acknowledged_at
        ),
        resolved_at=incident.resolved_at,
    )


@router.post(
    "/{incident_id}/investigate",
    response_model=IncidentStatusUpdateResponse,
    summary="Mark incident as investigating",
)
def investigate_incident(
    incident_id: str,
    service: IncidentService = Depends(
        get_incident_service
    ),
) -> IncidentStatusUpdateResponse:
    try:
        incident = (
            service.investigate_incident(
                incident_id
            )
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return IncidentStatusUpdateResponse(
        incident_id=incident.incident_id,
        status=incident.status,
        updated_at=incident.updated_at,
        acknowledged_at=(
            incident.acknowledged_at
        ),
        resolved_at=incident.resolved_at,
    )


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentStatusUpdateResponse,
    summary="Resolve incident",
)
def resolve_incident(
    incident_id: str,
    service: IncidentService = Depends(
        get_incident_service
    ),
) -> IncidentStatusUpdateResponse:
    try:
        incident = service.resolve_incident(
            incident_id
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return IncidentStatusUpdateResponse(
        incident_id=incident.incident_id,
        status=incident.status,
        updated_at=incident.updated_at,
        acknowledged_at=(
            incident.acknowledged_at
        ),
        resolved_at=incident.resolved_at,
    )


@router.post(
    "/{incident_id}/false-positive",
    response_model=IncidentStatusUpdateResponse,
    summary="Mark incident as false positive",
)
def mark_false_positive(
    incident_id: str,
    service: IncidentService = Depends(
        get_incident_service
    ),
) -> IncidentStatusUpdateResponse:
    try:
        incident = (
            service.mark_false_positive(
                incident_id
            )
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return IncidentStatusUpdateResponse(
        incident_id=incident.incident_id,
        status=incident.status,
        updated_at=incident.updated_at,
        acknowledged_at=(
            incident.acknowledged_at
        ),
        resolved_at=incident.resolved_at,
    )
