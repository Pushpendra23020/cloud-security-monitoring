from botocore.exceptions import BotoCoreError, ClientError
from boto3.session import Session

from app.collectors.aws.session import get_aws_session


class EC2CollectorError(Exception):
    pass


def collect_ec2_instances(
    session: Session | None = None,
) -> list[dict]:
    try:
        aws_session = session or get_aws_session()
        client = aws_session.client("ec2")

        paginator = client.get_paginator("describe_instances")

        assets = []

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):

                    name = None

                    for tag in instance.get("Tags", []):
                        if tag.get("Key") == "Name":
                            name = tag.get("Value")
                            break

                    assets.append(
                        {
                            "asset_type": "ec2_instance",
                            "asset_id": instance["InstanceId"],
                            "name": name,
                            "region": aws_session.region_name,
                            "state": instance.get("State", {}).get("Name"),
                            "instance_type": instance.get("InstanceType"),
                            "private_ip": instance.get("PrivateIpAddress"),
                            "public_ip": instance.get("PublicIpAddress"),
                        }
                    )

        return assets

    except (ClientError, BotoCoreError) as exc:
        raise EC2CollectorError(
            f"Failed to collect EC2 instances: {exc}"
        ) from exc
