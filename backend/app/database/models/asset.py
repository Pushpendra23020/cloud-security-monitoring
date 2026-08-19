from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)

from app.database.base import Base


class Asset(Base):

    __tablename__ = "assets"

    id = Column(
        Integer,
        primary_key=True,
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
        unique=True,
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
