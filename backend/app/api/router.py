from fastapi import APIRouter
from app.api.v1.incidents import router as incidents_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.aws import router as aws_router
from app.api.v1.cloud_accounts import router as cloud_accounts_router
from app.api.v1.health import router as health_router
from app.api.v1.statistics import router as statistics_router


api_router = APIRouter(
    prefix="/api/v1"
)

api_router.include_router(
    health_router
)

api_router.include_router(
    cloud_accounts_router
)

api_router.include_router(
    aws_router
)

api_router.include_router(
    alerts_router
)

api_router.include_router(
    statistics_router
)
api_router.include_router(
    incidents_router
)