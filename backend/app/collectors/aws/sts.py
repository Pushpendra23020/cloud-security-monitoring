from typing import TypedDict

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

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

