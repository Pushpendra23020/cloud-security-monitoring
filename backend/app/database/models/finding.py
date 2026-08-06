from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from app.database.base import Base


class Finding(Base):

    __tablename__ = "findings"


    id = Column(
        Integer,
        primary_key=True
    )


    asset_id = Column(
        Integer,
        ForeignKey("assets.id")
    )


    title = Column(
        String,
        nullable=False
    )


    description = Column(
        Text
    )


    severity = Column(
        String
    )


    status = Column(
        String,
        default="open"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )