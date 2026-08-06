from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.base import Base


class CloudAccount(Base):

    __tablename__ = "cloud_accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    provider = Column(
        String,
        nullable=False
    )

    account_id = Column(
        String,
        unique=True,
        nullable=False
    )

    region = Column(
        String
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )