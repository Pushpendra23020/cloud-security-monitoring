from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.dashboard_service import (
    DashboardService,
)
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    RecentAlertsResponse,
    RecentIncidentsResponse,
    RiskSummaryResponse,
    SeverityDistributionResponse,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def get_dashboard_service(
    db: Session = Depends(get_db),
) -> DashboardService:
    return DashboardService(
        db=db
    )


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get security dashboard summary",
)
def get_dashboard_summary(
    service: DashboardService = Depends(
        get_dashboard_service
    ),
) -> DashboardSummaryResponse:
    return service.get_summary()
@router.get(
    "/severity-distribution",
    response_model=SeverityDistributionResponse,
)
def get_severity_distribution(
    service: DashboardService = Depends(
        get_dashboard_service
    ),
) -> SeverityDistributionResponse:
    return service.get_severity_distribution()


@router.get(
    "/risk-summary",
    response_model=RiskSummaryResponse,
)
def get_risk_summary(
    service: DashboardService = Depends(
        get_dashboard_service
    ),
) -> RiskSummaryResponse:
    return service.get_risk_summary()


@router.get(
    "/recent-alerts",
    response_model=RecentAlertsResponse,
)
def get_recent_alerts(
    limit: int = 6,
    service: DashboardService = Depends(
        get_dashboard_service
    ),
) -> RecentAlertsResponse:
    limit = max(
        1,
        min(limit, 50),
    )

    return service.get_recent_alerts(
        limit=limit
    )


@router.get(
    "/recent-incidents",
    response_model=RecentIncidentsResponse,
)
def get_recent_incidents(
    limit: int = 6,
    service: DashboardService = Depends(
        get_dashboard_service
    ),
) -> RecentIncidentsResponse:
    limit = max(
        1,
        min(limit, 50),
    )

    return service.get_recent_incidents(
        limit=limit
    )
