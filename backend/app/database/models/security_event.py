from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SecurityEventRecord(Base):
    __tablename__ = "security_events"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "event_id",
            name="uq_security_events_org_event",
        ),
        CheckConstraint(
            "status IN ('queued', 'processing', 'retry', 'completed', 'dead_letter')",
            name="ck_security_events_status",
        ),
        CheckConstraint("attempts >= 0", name="ck_security_events_attempts"),
        CheckConstraint("max_attempts > 0", name="ck_security_events_max_attempts"),
        Index(
            "ix_security_events_org_queue",
            "organization_id",
            "status",
            "available_at",
            "received_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="cloudtrail")
    raw_event: Mapped[dict] = mapped_column(JSON, nullable=False)
    normalized_event: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(255))
    last_error: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archive_uri: Mapped[str | None] = mapped_column(String(2048))
    archive_sha256: Mapped[str | None] = mapped_column(String(64))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archive_retention_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
