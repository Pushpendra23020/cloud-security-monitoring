from app.models.security_event import SecurityEvent


def classify_event(event: SecurityEvent) -> SecurityEvent:
    event_name = event.event_name.lower()
    error_code = (event.error_code or "").lower()

    # Default
    severity = "info"

    # Failed authentication
    if event_name == "consolelogin" and event.success is False:
        severity = "medium"

    # Access denied / authorization failures
    if "accessdenied" in error_code or "unauthorized" in error_code:
        severity = "medium"

    # IAM/security-sensitive changes
    high_risk_events = {
        "createuser",
        "deleteuser",
        "createaccesskey",
        "deleteaccesskey",
        "attachuserpolicy",
        "attachrolepolicy",
        "putuserpolicy",
        "putrolepolicy",
        "updateassumerolepolicy",
    }

    if event_name in high_risk_events:
        severity = "high"

    # Very sensitive account/security changes
    critical_events = {
        "stoplogging",
        "deletetrail",
        "disablekey",
        "schedulekeydeletion",
        "deleteaccountpasswordpolicy",
    }

    if event_name in critical_events:
        severity = "critical"

    event.severity = severity

    return event
