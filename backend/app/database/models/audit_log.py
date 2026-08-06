from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.base import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"


    id = Column(
        Integer,
        primary_key=True
    )


    action = Column(
        String
    )


    user = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )