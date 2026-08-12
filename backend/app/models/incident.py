from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertSeverity


class IncidentStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Incident(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True
    )

    incident_id: str = Field(
        default_factory=lambda: (
            f"incident-{uuid4()}"
        )
    )

    title: str
    description: Optional[str] = None

    severity: AlertSeverity
    status: IncidentStatus = (
        IncidentStatus.OPEN
    )

    cloud_provider: str

    account_id: Optional[str] = None
    region: Optional[str] = None

    source_ip: Optional[str] = None
    user_identity: Optional[str] = None

    correlation_rule_id: Optional[str] = None

    alert_ids: List[str] = Field(
        default_factory=list
    )

    event_ids: List[str] = Field(
        default_factory=list
    )

    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_technique_id: Optional[str] = None

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
