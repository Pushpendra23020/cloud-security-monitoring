import boto3


def create_aws_session(
    profile_name: str | None = None,
    region_name: str = "us-east-1",
):
    session_kwargs = {
        "region_name": region_name,
    }

    if profile_name:
        session_kwargs["profile_name"] = (
            profile_name
        )

    return boto3.Session(
        **session_kwargs
    )


def create_cloudtrail_client(
    profile_name: str | None = None,
    region_name: str = "us-east-1",
):
    session = create_aws_session(
        profile_name=profile_name,
        region_name=region_name,
    )

    return session.client(
        "cloudtrail"
    )
