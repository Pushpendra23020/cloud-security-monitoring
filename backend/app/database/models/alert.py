from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # alert_id: Mapped[str] = mapped_column(
    #     String(36),
    #     unique=True,
    #     nullable=False,
    #     index=True,
    # )
    alert_id: Mapped[str] = mapped_column(
    String(100),
    unique=True,
    nullable=False,
    index=True,
    )

    rule_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    rule_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    event_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    detection_key: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    cloud_provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    account_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    service: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_ip: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    user_identity: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    resource_type: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
    index=True,
   )

    resource_id: Mapped[str | None] = mapped_column(
    String(255),
    nullable=True,
    index=True,
   )
    incident_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        index=True,
    )

    mitre_tactic: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    mitre_technique: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mitre_technique_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
