from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)

from app.database.base import Base


class Asset(Base):

    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("organization_id", "asset_id", name="uq_assets_org_asset"),
        UniqueConstraint("organization_id", "id", name="uq_assets_org_id"),
        ForeignKeyConstraint(
            ["organization_id", "cloud_account_id"],
            ["cloud_accounts.organization_id", "cloud_accounts.id"],
            name="fk_assets_org_cloud_account",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        default=1,
        index=True,
    )

    cloud_account_id = Column(
        Integer,
        ForeignKey("cloud_accounts.id"),
        nullable=False,
    )

    asset_type = Column(
        String,
        nullable=False,
    )

    asset_id = Column(
        String,
        nullable=False,
    )

    name = Column(
        String,
        nullable=True,
    )

    region = Column(
        String,
        nullable=True,
    )

    risk_score = Column(
        Integer,
        nullable=False,
        default=0,
    )

    risk_level = Column(
        String,
        nullable=False,
        default="low",
    )

    findings_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    alerts_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    public_exposure = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    resource_state = Column(
        String,
        nullable=False,
        default="unknown",
    )

    tags = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    last_seen = Column(
        DateTime,
        nullable=True,
    )
    risk_updated_at = Column(
    DateTime,
    nullable=True,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
