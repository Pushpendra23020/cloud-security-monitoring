from datetime import datetime
from typing import Any, Dict

from app.models.security_event import SecurityEvent


def normalize_cloudtrail_event(event: Dict[str, Any]) -> SecurityEvent:
    event_source = event.get("eventSource", "")
    service = event_source.split(".")[0] if event_source else None

    user_identity = event.get("userIdentity") or {}

    username = (
        user_identity.get("userName")
        or user_identity.get("principalId")
        or user_identity.get("arn")
    )

    success = not bool(event.get("errorCode"))

    return SecurityEvent(
        event_id=event.get("eventID"),
        timestamp=datetime.fromisoformat(
            event["eventTime"].replace("Z", "+00:00")
        ),
        cloud_provider="aws",
        account_id=user_identity.get("accountId"),
        region=event.get("awsRegion"),
        service=service,
        event_name=event.get("eventName", "UnknownEvent"),
        event_category=event.get("eventType"),
        source_ip=event.get("sourceIPAddress"),
        user_identity=username,
        success=success,
        error_code=event.get("errorCode"),
        error_message=event.get("errorMessage"),
        raw_event=event,
    )
