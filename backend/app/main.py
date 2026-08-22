from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.config import settings
from app.database.session import engine


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.include_router(api_router)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "message": "Cloud Security Monitoring API",
        "version": settings.APP_VERSION,
        "status": "running",
    }


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
