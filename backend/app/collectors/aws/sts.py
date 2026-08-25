from typing import TypedDict

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

import boto3

from app.collectors.aws.session import get_aws_session


class AWSIdentity(TypedDict):
    user_id: str
    account_id: str
    arn: str


class AWSConnectionError(Exception):
    """Raised when AWS identity verification fails."""


def get_caller_identity() -> AWSIdentity:
    try:
        session = get_aws_session()
        sts_client = session.client("sts")

        response = sts_client.get_caller_identity()

        return {
            "user_id": response["UserId"],
            "account_id": response["Account"],
            "arn": response["Arn"],
        }

    except NoCredentialsError as exc:
        raise AWSConnectionError(
            "AWS credentials were not found."
        ) from exc

    except PartialCredentialsError as exc:
        raise AWSConnectionError(
            "AWS credentials are incomplete."
        ) from exc

    except ClientError as exc:
        error_message = exc.response.get(
            "Error",
            {},
        ).get(
            "Message",
            "AWS rejected the request.",
        )

        raise AWSConnectionError(error_message) from exc

    except BotoCoreError as exc:
        raise AWSConnectionError(
            "An AWS SDK connection error occurred."
        ) from exc


def assume_role_identity(role_arn: str, region: str, external_id: str | None = None) -> AWSIdentity:
    """Validate cross-account access using short-lived STS credentials."""
    try:
        arguments = {"RoleArn": role_arn, "RoleSessionName": "cloud-security-monitor"}
        if external_id:
            arguments["ExternalId"] = external_id
        response = get_aws_session().client("sts", region_name=region).assume_role(**arguments)
        credentials = response["Credentials"]
        session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=region,
        )
        identity = session.client("sts").get_caller_identity()
        return {"user_id": identity["UserId"], "account_id": identity["Account"], "arn": identity["Arn"]}
    except (NoCredentialsError, PartialCredentialsError, ClientError, BotoCoreError) as exc:
        raise AWSConnectionError("Unable to assume the configured monitoring role.") from exc
