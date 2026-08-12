from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertSeverity
from app.models.incident import IncidentStatus
from app.schemas.alert import AlertResponse


class IncidentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    incident_id: str
    title: str
    description: Optional[str] = None

    severity: AlertSeverity
    status: IncidentStatus

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

    created_at: datetime
    updated_at: datetime

    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class IncidentListResponse(BaseModel):
    items: List[IncidentResponse]
    total: int


class IncidentStatusUpdateResponse(BaseModel):
    incident_id: str
    status: IncidentStatus
    updated_at: datetime

    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class IncidentAlertsResponse(BaseModel):
    incident_id: str
    items: List[AlertResponse]
    total: int
