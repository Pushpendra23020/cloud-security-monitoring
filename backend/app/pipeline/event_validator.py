from app.models.security_event import SecurityEvent


class InvalidSecurityEvent(Exception):
    pass


def validate_event(event: SecurityEvent) -> SecurityEvent:
    if not event.event_id:
        raise InvalidSecurityEvent("event_id is required")

    if not event.event_name:
        raise InvalidSecurityEvent("event_name is required")

    if not event.cloud_provider:
        raise InvalidSecurityEvent("cloud_provider is required")

    if not event.timestamp:
        raise InvalidSecurityEvent("timestamp is required")

    supported_providers = {
        "aws",
        "azure",
        "gcp",
    }

    if event.cloud_provider.lower() not in supported_providers:
        raise InvalidSecurityEvent(
            f"Unsupported cloud provider: {event.cloud_provider}"
        )

    valid_severities = {
        "info",
        "low",
        "medium",
        "high",
        "critical",
    }

    if event.severity.lower() not in valid_severities:
        raise InvalidSecurityEvent(
            f"Invalid severity: {event.severity}"
        )

    return event

