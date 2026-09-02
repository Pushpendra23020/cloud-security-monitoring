from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "account_id", name="uq_cloud_accounts_org_account"),
        UniqueConstraint("organization_id", "id", name="uq_cloud_accounts_org_id"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, default=1, index=True
    )

    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="AWS Account")
    auth_method: Mapped[str] = mapped_column(String(30), nullable=False, default="assume_role")
    role_arn: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    services: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
