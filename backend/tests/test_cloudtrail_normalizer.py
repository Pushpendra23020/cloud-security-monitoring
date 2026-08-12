import json
from pathlib import Path

from app.normalizers.aws.cloudtrail import normalize_cloudtrail_event


def test_normalize_cloudtrail_console_login():
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "aws"
        / "cloudtrail_console_login.json"
    )

    with fixture_path.open() as file:
        raw_event = json.load(file)

    event = normalize_cloudtrail_event(raw_event)

    assert event.cloud_provider == "aws"
    assert event.account_id == "123456789012"
    assert event.region == "us-east-1"
    assert event.service == "signin"
    assert event.event_name == "ConsoleLogin"
    assert event.user_identity == "admin"
    assert event.source_ip == "203.0.113.50"
    assert event.success is True
    assert event.event_id == "11111111-2222-3333-4444-555555555555"


def test_normalize_failed_cloudtrail_login():
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "aws"
        / "cloudtrail_failed_login.json"
    )

    with fixture_path.open() as file:
        raw_event = json.load(file)

    event = normalize_cloudtrail_event(raw_event)

    assert event.cloud_provider == "aws"
    assert event.event_name == "ConsoleLogin"
    assert event.user_identity == "test-user"
    assert event.source_ip == "198.51.100.25"
    assert event.success is False
    assert event.error_code == "FailedAuthentication"
    assert event.error_message == "Authentication failed"
