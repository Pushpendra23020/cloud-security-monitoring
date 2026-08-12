from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings


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
