from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.base import Base


class Alert(Base):

    __tablename__ = "alerts"


    id = Column(
        Integer,
        primary_key=True
    )


    severity = Column(
        String
    )


    message = Column(
        String
    )


    status = Column(
        String,
        default="new"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )