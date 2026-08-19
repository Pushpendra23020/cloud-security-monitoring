import time
from typing import Any

import httpx

from app.models.alert import Alert
from app.notifications.base import (
    AlertNotifier,
)


class WebhookNotifier(AlertNotifier):

    RETRYABLE_STATUS_CODES = {
        408,
        425,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        url: str,
        *,
        timeout: float = 5.0,
        headers: dict[str, str] | None = None,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ):
        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be >= 1"
            )

        if backoff_seconds < 0:
            raise ValueError(
                "backoff_seconds must be >= 0"
            )

        self.url = url
        self.timeout = timeout
        self.headers = headers or {}
        self.max_attempts = max_attempts
        self.backoff_seconds = (
            backoff_seconds
        )

    @staticmethod
    def build_payload(
        alert: Alert,
    ) -> dict[str, Any]:
        return {
            "alert_id": alert.alert_id,
            "rule_id": alert.rule_id,
            "rule_name": alert.rule_name,
            "description": alert.description,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "event_id": alert.event_id,
            "event_name": alert.event_name,
            "cloud_provider": (
                alert.cloud_provider
            ),
            "account_id": alert.account_id,
            "region": alert.region,
            "service": alert.service,
            "source_ip": alert.source_ip,
            "user_identity": (
                alert.user_identity
            ),
            "resource_type": (
                alert.resource_type
            ),
            "resource_id": alert.resource_id,
            "incident_id": alert.incident_id,
            "occurrence_count": (
                alert.occurrence_count
            ),
            "first_seen_at": (
                alert.first_seen_at.isoformat()
            ),
            "last_seen_at": (
                alert.last_seen_at.isoformat()
            ),
            "mitre_tactic": alert.mitre_tactic,
            "mitre_technique": (
                alert.mitre_technique
            ),
            "mitre_technique_id": (
                alert.mitre_technique_id
            ),
            "metadata": alert.metadata,
        }

    @classmethod
    def _is_retryable_status(
        cls,
        status_code: int,
    ) -> bool:
        return (
            status_code
            in cls.RETRYABLE_STATUS_CODES
        )

    def _record_attempt(
        self,
        alert: Alert,
        *,
        attempt: int,
        success: bool,
        status_code: int | None = None,
        error: str | None = None,
    ) -> None:
        alert.metadata[
            "webhook_delivery"
        ] = {
            "attempt": attempt,
            "success": success,
            "status_code": status_code,
            "error": error,
        }

    def send(
        self,
        alert: Alert,
    ) -> bool:
        payload = self.build_payload(
            alert
        )

        for attempt in range(
            1,
            self.max_attempts + 1,
        ):
            try:
                response = httpx.post(
                    self.url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )

                status_code = (
                    response.status_code
                )

                if 200 <= status_code < 300:
                    self._record_attempt(
                        alert,
                        attempt=attempt,
                        success=True,
                        status_code=status_code,
                    )

                    return True

                if not self._is_retryable_status(
                    status_code
                ):
                    self._record_attempt(
                        alert,
                        attempt=attempt,
                        success=False,
                        status_code=status_code,
                        error=(
                            "non-retryable "
                            "HTTP response"
                        ),
                    )

                    return False

                self._record_attempt(
                    alert,
                    attempt=attempt,
                    success=False,
                    status_code=status_code,
                    error=(
                        "retryable HTTP response"
                    ),
                )

            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
                httpx.RemoteProtocolError,
            ) as exc:
                self._record_attempt(
                    alert,
                    attempt=attempt,
                    success=False,
                    error=type(exc).__name__,
                )

            except httpx.HTTPError as exc:
                self._record_attempt(
                    alert,
                    attempt=attempt,
                    success=False,
                    error=type(exc).__name__,
                )

                return False

            if attempt < self.max_attempts:
                delay = (
                    self.backoff_seconds
                    * (2 ** (attempt - 1))
                )

                time.sleep(delay)

        return False
