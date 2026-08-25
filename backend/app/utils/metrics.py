from prometheus_client import Counter, Gauge, Histogram, Info


APP_INFO = Info(
    "cloud_security_app",
    "Cloud Security Monitoring application information",
)

HTTP_REQUESTS_TOTAL = Counter(
    "cloud_security_http_requests_total",
    "Total number of HTTP requests",
    [
        "method",
        "path",
        "status_code",
    ],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "cloud_security_http_request_duration_seconds",
    "HTTP request duration in seconds",
    [
        "method",
        "path",
    ],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "cloud_security_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    [
        "method",
    ],
)


def initialize_app_metrics(
    *,
    version: str,
    environment: str,
) -> None:
    APP_INFO.info(
        {
            "version": version,
            "environment": environment,
        }
    )


# Security-domain metrics

SECURITY_DETECTIONS_TOTAL = Counter(
    "cloud_security_detections_total",
    "Total security detections produced",
    [
        "severity",
        "cloud_provider",
        "detection_type",
    ],
)

SECURITY_ALERTS_SAVED_TOTAL = Counter(
    "cloud_security_alerts_saved_total",
    "Total alerts successfully persisted",
    [
        "severity",
        "cloud_provider",
    ],
)

SECURITY_ALERTS_DEDUPLICATED_TOTAL = Counter(
    "cloud_security_alerts_deduplicated_total",
    "Total alerts merged or rejected as duplicates",
)

SECURITY_INCIDENTS_CREATED_TOTAL = Counter(
    "cloud_security_incidents_created_total",
    "Total security incidents created",
)

CLOUDTRAIL_EVENTS_TOTAL = Counter(
    "cloud_security_cloudtrail_events_total",
    "CloudTrail ingestion event totals",
    [
        "result",
    ],
)

ASSET_RISK_REFRESH_TOTAL = Counter(
    "cloud_security_asset_risk_refresh_total",
    "Asset risk refresh totals",
    [
        "result",
    ],
)

ASSET_RISK_REFRESH_BATCHES_TOTAL = Counter(
    "cloud_security_asset_risk_refresh_batches_total",
    "Total asset risk refresh batches completed",
)
