from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SecurityEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    cloud_provider: str
    account_id: Optional[str] = None
    region: Optional[str] = None

    service: Optional[str] = None
    event_name: str
    event_category: Optional[str] = None

    source_ip: Optional[str] = None
    user_identity: Optional[str] = None

    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    severity: str = "info"

    success: Optional[bool] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    raw_event: Dict[str, Any] = Field(default_factory=dict)
