from fastapi import APIRouter

from app.api.v1.aws import router as aws_router
from app.api.v1.cloud_accounts import router as cloud_accounts_router
from app.api.v1.health import router as health_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(cloud_accounts_router)
api_router.include_router(aws_router)
