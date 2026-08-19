from unittest.mock import (
    MagicMock,
    patch,
)

import httpx
import pytest

from app.models.alert import (
    Alert,
    AlertSeverity,
)
from app.notifications.webhook import (
    WebhookNotifier,
)


def build_alert():
    return Alert(
        rule_id="AWS-WEBHOOK-001",
        rule_name="Webhook Test Alert",
        severity=AlertSeverity.CRITICAL,
        event_id="event-webhook-001",
        event_name="DeleteBucket",
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        resource_type="s3",
        resource_id="important-bucket",
    )


def make_response(
    status_code: int,
):
    response = MagicMock()
    response.status_code = status_code
    return response


def test_build_payload():
    alert = build_alert()

    payload = (
        WebhookNotifier.build_payload(
            alert
        )
    )

    assert payload["alert_id"] == alert.alert_id
    assert payload["severity"] == "critical"
    assert (
        payload["resource_id"]
        == "important-bucket"
    )


@patch(
    "app.notifications.webhook.httpx.post"
)
def test_webhook_success(
    mock_post,
):
    mock_post.return_value = (
        make_response(200)
    )

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook"
    )

    result = notifier.send(alert)

    assert result is True
    assert mock_post.call_count == 1

    delivery = alert.metadata[
        "webhook_delivery"
    ]

    assert delivery["success"] is True
    assert delivery["attempt"] == 1
    assert delivery["status_code"] == 200


@patch(
    "app.notifications.webhook.time.sleep"
)
@patch(
    "app.notifications.webhook.httpx.post"
)
def test_retry_then_success(
    mock_post,
    mock_sleep,
):
    mock_post.side_effect = [
        make_response(503),
        make_response(200),
    ]

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook",
        max_attempts=3,
        backoff_seconds=1.0,
    )

    result = notifier.send(alert)

    assert result is True
    assert mock_post.call_count == 2

    mock_sleep.assert_called_once_with(
        1.0
    )

    delivery = alert.metadata[
        "webhook_delivery"
    ]

    assert delivery["success"] is True
    assert delivery["attempt"] == 2


@patch(
    "app.notifications.webhook.time.sleep"
)
@patch(
    "app.notifications.webhook.httpx.post"
)
def test_exponential_backoff(
    mock_post,
    mock_sleep,
):
    mock_post.side_effect = [
        make_response(503),
        make_response(503),
        make_response(200),
    ]

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook",
        max_attempts=3,
        backoff_seconds=2.0,
    )

    assert notifier.send(alert) is True

    assert (
        mock_sleep.call_args_list[0].args[0]
        == 2.0
    )

    assert (
        mock_sleep.call_args_list[1].args[0]
        == 4.0
    )


@patch(
    "app.notifications.webhook.time.sleep"
)
@patch(
    "app.notifications.webhook.httpx.post"
)
def test_retryable_http_failure_exhausts_attempts(
    mock_post,
    mock_sleep,
):
    mock_post.return_value = (
        make_response(503)
    )

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook",
        max_attempts=3,
        backoff_seconds=0.1,
    )

    result = notifier.send(alert)

    assert result is False
    assert mock_post.call_count == 3
    assert mock_sleep.call_count == 2

    delivery = alert.metadata[
        "webhook_delivery"
    ]

    assert delivery["success"] is False
    assert delivery["attempt"] == 3
    assert delivery["status_code"] == 503


@patch(
    "app.notifications.webhook.time.sleep"
)
@patch(
    "app.notifications.webhook.httpx.post"
)
def test_400_is_not_retried(
    mock_post,
    mock_sleep,
):
    mock_post.return_value = (
        make_response(400)
    )

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook"
    )

    result = notifier.send(alert)

    assert result is False
    assert mock_post.call_count == 1
    mock_sleep.assert_not_called()


@patch(
    "app.notifications.webhook.time.sleep"
)
@patch(
    "app.notifications.webhook.httpx.post"
)
def test_429_is_retried(
    mock_post,
    mock_sleep,
):
    mock_post.side_effect = [
        make_response(429),
        make_response(200),
    ]

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook",
        max_attempts=2,
        backoff_seconds=1.0,
    )

    assert notifier.send(alert) is True
    assert mock_post.call_count == 2


@patch(
    "app.notifications.webhook.time.sleep"
)
@patch(
    "app.notifications.webhook.httpx.post"
)
def test_connection_error_is_retried(
    mock_post,
    mock_sleep,
):
    mock_post.side_effect = [
        httpx.ConnectError(
            "connection failed"
        ),
        make_response(200),
    ]

    alert = build_alert()

    notifier = WebhookNotifier(
        "https://example.com/webhook",
        max_attempts=2,
        backoff_seconds=1.0,
    )

    result = notifier.send(alert)

    assert result is True
    assert mock_post.call_count == 2


def test_invalid_max_attempts():
    with pytest.raises(
        ValueError,
        match="max_attempts",
    ):
        WebhookNotifier(
            "https://example.com/webhook",
            max_attempts=0,
        )


def test_invalid_backoff():
    with pytest.raises(
        ValueError,
        match="backoff_seconds",
    ):
        WebhookNotifier(
            "https://example.com/webhook",
            backoff_seconds=-1,
        )
