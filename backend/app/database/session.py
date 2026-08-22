from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def build_database_url():
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


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
