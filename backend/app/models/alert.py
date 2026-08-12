from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Alert(BaseModel):
    alert_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Detection rule information
    rule_id: str
    rule_name: str
    description: Optional[str] = None

    severity: str

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

    # Alert lifecycle
    status: str = "open"

    # MITRE ATT&CK metadata
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_technique_id: Optional[str] = None

    # Additional detection context
    metadata: Dict[str, Any] = Field(default_factory=dict)
