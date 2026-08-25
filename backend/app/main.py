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
from app.database.session import SessionLocal, engine
from app.database.models.user import User
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.auth import AuditMiddleware, AuthenticationMiddleware
from app.utils.logger import configure_logging, get_logger
from app.utils.metrics import initialize_app_metrics



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
            changed = False
            if not verify_password(password, user.password_hash):
                user.password_hash = hash_password(password)
                changed = True
            if user.email != email:
                user.email = email
                changed = True
            if user.role != "admin" or not user.is_active:
                user.role = "admin"
                user.is_active = True
                changed = True
            if changed:
                db.commit()
                logger.info(
                    "Phase 10 bootstrap administrator synchronized",
                    extra={"username": username},
                )
            return
        repository.add(
            User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role="admin",
            )
        )
        logger.info("Phase 10 bootstrap administrator created", extra={"username": username})


@asynccontextmanager
async def lifespan(_: FastAPI):
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
