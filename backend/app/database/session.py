from collections.abc import Generator
import re

from fastapi import Request
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.tenancy import DEFAULT_ORGANIZATION_ID


TENANT_SETTING = "app.current_organization_id"
RLS_TABLES = (
    "cloud_accounts",
    "assets",
    "findings",
    "alerts",
    "incidents",
    "audit_logs",
    "security_events",
)
_ROLE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def build_database_url(*, for_migrations: bool = False):
    if for_migrations and settings.MIGRATION_DATABASE_URL:
        return settings.MIGRATION_DATABASE_URL

    if (
        settings.POSTGRES_DB
        and settings.POSTGRES_USER
        and settings.POSTGRES_PASSWORD
    ):
        return URL.create(
            drivername="postgresql+psycopg2",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
        )

    if settings.DATABASE_URL:
        return settings.DATABASE_URL

    raise RuntimeError(
        "Database configuration is missing. "
        "Set DATABASE_URL or POSTGRES_DB/POSTGRES_USER/"
        "POSTGRES_PASSWORD."
    )


engine = create_engine(
    build_database_url(),
    pool_pre_ping=True,
)


if settings.DATABASE_RUNTIME_ROLE:
    if not _ROLE_PATTERN.fullmatch(settings.DATABASE_RUNTIME_ROLE):
        raise RuntimeError(
            "DATABASE_RUNTIME_ROLE must be a valid PostgreSQL role identifier."
        )

    @event.listens_for(engine, "connect")
    def _assume_runtime_role(dbapi_connection, _connection_record) -> None:
        with dbapi_connection.cursor() as cursor:
            cursor.execute(f'SET ROLE "{settings.DATABASE_RUNTIME_ROLE}"')


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def set_tenant_context(db: Session, organization_id: int) -> None:
    """Bind a session and all of its future transactions to one organization."""

    if isinstance(organization_id, bool) or organization_id <= 0:
        raise ValueError("organization_id must be a positive integer")

    existing = db.info.get(TENANT_SETTING)
    if existing is not None and existing != organization_id and db.in_transaction():
        raise RuntimeError("Cannot change tenant context during an active transaction.")

    db.info[TENANT_SETTING] = organization_id
    if db.in_transaction():
        db.execute(
            text("SELECT set_config(:setting, :organization_id, true)"),
            {
                "setting": TENANT_SETTING,
                "organization_id": str(organization_id),
            },
        )


@event.listens_for(Session, "after_begin")
def _apply_tenant_context(session: Session, _transaction, connection) -> None:
    organization_id = session.info.get(TENANT_SETTING)
    if organization_id is None:
        return
    if connection.dialect.name != "postgresql":
        return
    connection.execute(
        text("SELECT set_config(:setting, :organization_id, true)"),
        {
            "setting": TENANT_SETTING,
            "organization_id": str(organization_id),
        },
    )


def get_rls_status() -> dict[str, object]:
    with engine.connect() as connection:
        role = connection.execute(
            text(
                """
                SELECT current_user, rolsuper, rolbypassrls
                FROM pg_roles
                WHERE rolname = current_user
                """
            )
        ).one()
        rows = connection.execute(
            text(
                """
                SELECT relname, relrowsecurity, relforcerowsecurity
                FROM pg_class
                WHERE relname = ANY(:tables)
                ORDER BY relname
                """
            ),
            {"tables": list(RLS_TABLES)},
        ).all()
    return {
        "role": role.current_user,
        "is_superuser": role.rolsuper,
        "bypasses_rls": role.rolbypassrls,
        "tables": {
            row.relname: {
                "enabled": row.relrowsecurity,
                "forced": row.relforcerowsecurity,
            }
            for row in rows
        },
    }


def validate_rls_enforcement() -> None:
    if not settings.RLS_ENFORCEMENT_REQUIRED:
        return
    status = get_rls_status()
    missing = [
        table
        for table in RLS_TABLES
        if not status["tables"].get(table, {}).get("enabled")
        or not status["tables"].get(table, {}).get("forced")
    ]
    if missing:
        raise RuntimeError(
            "PostgreSQL row-level security is not enabled and forced for: "
            + ", ".join(missing)
        )
    if status["is_superuser"] or status["bypasses_rls"]:
        raise RuntimeError(
            "The application database role can bypass PostgreSQL row-level security."
        )


def get_db(request: Request) -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        organization_id = getattr(request.state, "organization_id", None)
        if organization_id is None and settings.ENVIRONMENT.lower() == "test" and not settings.AUTH_ENABLED:
            organization_id = DEFAULT_ORGANIZATION_ID
        if organization_id is not None:
            set_tenant_context(db, organization_id)
        yield db
    finally:
        db.close()
