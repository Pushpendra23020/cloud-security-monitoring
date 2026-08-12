import boto3
from boto3.session import Session

from app.config import settings


def get_aws_session() -> Session:
    session_options: dict[str, str] = {
        "region_name": settings.AWS_REGION,
    }

    if settings.AWS_PROFILE:
        session_options["profile_name"] = settings.AWS_PROFILE

    return boto3.Session(**session_options)
