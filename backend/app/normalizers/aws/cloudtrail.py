from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.models.security_event import SecurityEvent


def extract_resource_context(
    event: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract a primary AWS resource type and resource ID
    from a CloudTrail event.

    This supports:
    - CloudTrail Resources[]
    - EC2 instance IDs
    - S3 bucket names
    - IAM users
    - IAM roles
    """

    #
    # 1. CloudTrail standard Resources array
    #
    resources = event.get("resources") or []

    if resources:
        first_resource = resources[0] or {}

        resource_arn = first_resource.get("ARN")
        resource_type = (
            first_resource.get("accountId")
            or first_resource.get("type")
        )

        if resource_arn:
            return (
                resource_type,
                resource_arn,
            )

    request_parameters = (
        event.get("requestParameters") or {}
    )

    event_name = event.get(
        "eventName",
        "",
    )

    service = (
        event.get("eventSource", "")
        .split(".")[0]
    )

    #
    # 2. EC2
    #
    instance_id = request_parameters.get(
        "instanceId"
    )

    if instance_id:
        return (
            "ec2_instance",
            instance_id,
        )

    instances_set = (
        request_parameters.get(
            "instancesSet"
        )
        or {}
    )

    items = (
        instances_set.get("items")
        or []
    )

    if items:
        first_instance = items[0] or {}

        instance_id = (
            first_instance.get(
                "instanceId"
            )
        )

        if instance_id:
            return (
                "ec2_instance",
                instance_id,
            )

    #
    # 3. S3
    #
    bucket_name = request_parameters.get(
        "bucketName"
    )

    if bucket_name:
        return (
            "s3_bucket",
            bucket_name,
        )

    #
    # 4. IAM User
    #
    user_name = request_parameters.get(
        "userName"
    )

    if (
        user_name
        and service == "iam"
    ):
        return (
            "iam_user",
            user_name,
        )

    #
    # 5. IAM Role
    #
    role_name = request_parameters.get(
        "roleName"
    )

    if (
        role_name
        and service == "iam"
    ):
        return (
            "iam_role",
            role_name,
        )

    #
    # 6. Some events identify a resource by name only.
    #
    if (
        service == "cloudtrail"
        and request_parameters.get(
            "name"
        )
    ):
        return (
            "cloudtrail_trail",
            request_parameters["name"],
        )

    #
    # No resource could be confidently identified.
    #
    return (
        None,
        None,
    )


def normalize_cloudtrail_event(
    event: Dict[str, Any],
) -> SecurityEvent:
    event_source = event.get(
        "eventSource",
        "",
    )

    service = (
        event_source.split(".")[0]
        if event_source
        else None
    )

    user_identity = (
        event.get("userIdentity")
        or {}
    )

    username = (
        user_identity.get("userName")
        or user_identity.get("principalId")
        or user_identity.get("arn")
    )

    success = not bool(
        event.get("errorCode")
    )

    resource_type, resource_id = (
        extract_resource_context(
            event
        )
    )

    return SecurityEvent(
        event_id=event.get("eventID"),

        timestamp=datetime.fromisoformat(
            event["eventTime"].replace(
                "Z",
                "+00:00",
            )
        ),

        cloud_provider="aws",

        account_id=(
            user_identity.get(
                "accountId"
            )
        ),

        region=event.get(
            "awsRegion"
        ),

        service=service,

        event_name=event.get(
            "eventName",
            "UnknownEvent",
        ),

        event_category=event.get(
            "eventType"
        ),

        source_ip=event.get(
            "sourceIPAddress"
        ),

        user_identity=username,

        resource_type=resource_type,
        resource_id=resource_id,

        success=success,

        error_code=event.get(
            "errorCode"
        ),

        error_message=event.get(
            "errorMessage"
        ),

        raw_event=event,
    )
