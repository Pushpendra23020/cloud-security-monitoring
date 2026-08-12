from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertSeverity, AlertStatus


class AlertResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    alert_id: str

    rule_id: str
    rule_name: str
    description: Optional[str] = None

    severity: AlertSeverity
    status: AlertStatus

    event_id: str
    event_name: str

    detection_key: Optional[str] = None

    cloud_provider: str
    account_id: Optional[str] = None
    region: Optional[str] = None

    service: Optional[str] = None
    source_ip: Optional[str] = None
    user_identity: Optional[str] = None

    incident_id: Optional[str] = None

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


class AlertListResponse(BaseModel):
    items: List[AlertResponse]

    total: int

    page: int
    page_size: int

    pages: int


class AlertStatusUpdateResponse(BaseModel):
    alert_id: str
    status: AlertStatus
    updated_at: datetime

    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertStatisticsResponse(BaseModel):
    total: int

    open: int
    acknowledged: int
    investigating: int
    resolved: int
    false_positive: int

    info: int
    low: int
    medium: int
    high: int
    critical: int
