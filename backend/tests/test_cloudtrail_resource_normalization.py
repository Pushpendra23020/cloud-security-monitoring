from app.normalizers.aws.cloudtrail import (
    normalize_cloudtrail_event,
)


def base_event():
    return {
        "eventID": "event-1",
        "eventTime": "2026-08-16T10:00:00Z",
        "eventSource": "ec2.amazonaws.com",
        "eventName": "StopInstances",
        "eventType": "AwsApiCall",
        "awsRegion": "ap-south-1",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity": {
            "accountId": "123456789012",
            "userName": "admin",
        },
        "requestParameters": {},
    }


def test_extracts_ec2_instance_id():
    event = base_event()

    event["requestParameters"] = {
        "instancesSet": {
            "items": [
                {
                    "instanceId": "i-abc123"
                }
            ]
        }
    }

    normalized = normalize_cloudtrail_event(
        event
    )

    assert normalized.resource_type == (
        "ec2_instance"
    )

    assert normalized.resource_id == (
        "i-abc123"
    )


def test_extracts_s3_bucket():
    event = base_event()

    event["eventSource"] = (
        "s3.amazonaws.com"
    )

    event["eventName"] = "PutBucketPolicy"

    event["requestParameters"] = {
        "bucketName": "prod-security-bucket"
    }

    normalized = normalize_cloudtrail_event(
        event
    )

    assert normalized.resource_type == (
        "s3_bucket"
    )

    assert normalized.resource_id == (
        "prod-security-bucket"
    )


def test_extracts_iam_user():
    event = base_event()

    event["eventSource"] = (
        "iam.amazonaws.com"
    )

    event["eventName"] = "CreateUser"

    event["requestParameters"] = {
        "userName": "alice"
    }

    normalized = normalize_cloudtrail_event(
        event
    )

    assert normalized.resource_type == (
        "iam_user"
    )

    assert normalized.resource_id == (
        "alice"
    )


def test_no_resource_returns_none():
    event = base_event()

    normalized = normalize_cloudtrail_event(
        event
    )

    assert normalized.resource_type is None
    assert normalized.resource_id is None
