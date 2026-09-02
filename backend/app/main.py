from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.config import settings
from app.database.session import SessionLocal, engine, validate_rls_enforcement
from app.database.models.user import User
from app.core.security import hash_password
from app.core.runtime_security import validate_api_runtime_security
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.auth import AuditMiddleware, AuthenticationMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.utils.logger import configure_logging, get_logger
from app.utils.metrics import initialize_app_metrics
from app.services.event_queue_metrics_service import refresh_event_queue_metrics



configure_logging()

logger = get_logger(__name__)

frontend_directory = Path(os.getenv("FRONTEND_DIST_DIR", ""))
serve_frontend = bool(os.getenv("FRONTEND_DIST_DIR")) and frontend_directory.is_dir()


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            return FileResponse(Path(self.directory) / "index.html")
        return response

initialize_app_metrics(
    version=settings.APP_VERSION,
    environment=settings.ENVIRONMENT,
)


def bootstrap_phase_10_admin() -> None:
    if not settings.AUTH_ENABLED:
        return
    username = settings.AUTH_BOOTSTRAP_ADMIN_USERNAME
    email = settings.AUTH_BOOTSTRAP_ADMIN_EMAIL
    password = settings.AUTH_BOOTSTRAP_ADMIN_PASSWORD
    if not all((username, email, password)):
        logger.warning(
            "Authentication enabled without complete bootstrap admin settings"
        )
        return
    if len(password) < 12:
        logger.warning(
            "Bootstrap administrator password ignored because it is shorter than 12 characters"
        )
        return
    with SessionLocal() as db:
        repository = UserRepository(db)
        user = repository.get_by_username(username)
        if user:
            organization_repository = OrganizationRepository(db)
            membership = organization_repository.get_membership(
                user.id,
                1,
                active_only=False,
            )
            if membership is None:
                organization_repository.ensure_default_membership(
                    user,
                    role="admin",
                )
            logger.info(
                "Bootstrap administrator already exists; credentials were not changed",
                extra={"username": username},
            )
            return
        user = repository.add(
            User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role="admin",
            )
        )
        OrganizationRepository(db).ensure_default_membership(
            user,
            role="admin",
            reactivate=True,
        )
        logger.info("Phase 10 bootstrap administrator created", extra={"username": username})


def validate_runtime_security() -> None:
    """Backward-compatible import point used by existing callers and tests."""
    validate_api_runtime_security()


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_runtime_security()
    validate_rls_enforcement()
    bootstrap_phase_10_admin()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router)

logger.info(
    "Cloud Security Monitoring API initialized"
)


@app.get("/api-info", tags=["Root"])
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
    if not settings.METRICS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        refresh_event_queue_metrics()
    except SQLAlchemyError:
        logger.exception("event_queue_metrics_refresh_failed")
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


if serve_frontend:
    app.mount(
        "/",
        SPAStaticFiles(directory=frontend_directory, html=True),
        name="frontend",
    )
