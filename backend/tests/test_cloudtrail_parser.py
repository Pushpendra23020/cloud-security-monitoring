import json

from app.collectors.aws.cloudtrail_parser import parse_lookup_events


def test_parse_cloudtrail_lookup_event():
    raw_cloudtrail_event = {
        "eventVersion": "1.08",
        "eventID": "aws-event-001",
        "eventTime": "2026-08-09T12:00:00Z",
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "203.0.113.10",
        "userIdentity": {
            "type": "IAMUser",
            "accountId": "123456789012",
            "userName": "admin",
        },
    }

    lookup_event = {
        "EventId": "aws-event-001",
        "EventName": "ConsoleLogin",
        "CloudTrailEvent": json.dumps(raw_cloudtrail_event),
    }

    parsed = parse_lookup_events([lookup_event])

    assert len(parsed) == 1
    assert parsed[0]["eventID"] == "aws-event-001"
    assert parsed[0]["eventName"] == "ConsoleLogin"
    assert parsed[0]["eventSource"] == "signin.amazonaws.com"
