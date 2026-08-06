from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.database.base import Base


class Asset(Base):

    __tablename__ = "assets"

    id = Column(
        Integer,
        primary_key=True
    )

    cloud_account_id = Column(
        Integer,
        ForeignKey("cloud_accounts.id")
    )

    asset_type = Column(
        String,
        nullable=False
    )

    asset_id = Column(
        String,
        unique=True,
        nullable=False
    )

    name = Column(
        String
    )

    region = Column(
        String
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )