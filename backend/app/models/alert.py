from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class AlertSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class Alert(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True
    )

    alert_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    first_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    last_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Detection rule information
    rule_id: str
    rule_name: str
    description: Optional[str] = None

    severity: AlertSeverity

    # Original security event
    event_id: str
    event_name: str
    detection_key: Optional[str] = None

    cloud_provider: str
    account_id: Optional[str] = None
    region: Optional[str] = None

    service: Optional[str] = None
    source_ip: Optional[str] = None
    user_identity: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    # Correlation / incident information
    incident_id: Optional[str] = None

    # Alert lifecycle
    status: AlertStatus = AlertStatus.OPEN

    # Deduplication / aggregation
    fingerprint: Optional[str] = None
    occurrence_count: int = Field(
        default=1,
        ge=1,
    )

    # Notification lifecycle
    notification_status: NotificationStatus = (
        NotificationStatus.PENDING
    )
    last_notified_at: Optional[datetime] = None
    suppressed_until: Optional[datetime] = None

    # MITRE ATT&CK metadata
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_technique_id: Optional[str] = None

    # Additional detection context
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )
