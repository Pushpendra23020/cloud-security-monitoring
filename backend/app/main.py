from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.config import settings
from app.database.session import engine
from app.middleware.logging import RequestLoggingMiddleware
from app.utils.logger import configure_logging, get_logger
from app.utils.metrics import initialize_app_metrics
from app.utils.metrics import initialize_app_metrics



configure_logging()

logger = get_logger(__name__)

initialize_app_metrics(
    version=settings.APP_VERSION,
    environment=settings.ENVIRONMENT,
)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router)

logger.info(
    "Cloud Security Monitoring API initialized"
)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "message": "Cloud Security Monitoring API",
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get(
    "/metrics",
    include_in_schema=False,
)
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/ready", tags=["Health"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {
        "status": "ready",
        "database": "connected",
    }
