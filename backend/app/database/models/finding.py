from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, ForeignKeyConstraint
from datetime import datetime

from app.database.base import Base


class Finding(Base):

    __tablename__ = "findings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "asset_id"],
            ["assets.organization_id", "assets.id"],
            name="fk_findings_org_asset",
        ),
    )


    id = Column(
        Integer,
        primary_key=True
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        default=1,
        index=True,
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
