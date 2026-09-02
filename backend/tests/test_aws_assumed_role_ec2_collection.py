from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.collectors.aws.ec2 import collect_ec2_instances
from app.collectors.aws.sts import assume_role_session
from app.services.aws_ingestion_service import AWSIngestionService


def test_assume_role_session_builds_temporary_credential_session():
    platform_session = MagicMock()
    sts_client = platform_session.client.return_value
    sts_client.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "temporary-access-key",
            "SecretAccessKey": "temporary-secret-key",
            "SessionToken": "temporary-session-token",
        }
    }
    assumed_session = MagicMock()

    with patch(
        "app.collectors.aws.sts.get_aws_session",
        return_value=platform_session,
    ), patch(
        "app.collectors.aws.sts.boto3.Session",
        return_value=assumed_session,
    ) as session_factory:
        result = assume_role_session(
            "arn:aws:iam::123456789012:role/CloudMonitor",
            "ap-south-1",
            "tenant-external-id",
        )

    assert result is assumed_session
    platform_session.client.assert_called_once_with(
        "sts",
        region_name="ap-south-1",
    )
    sts_client.assume_role.assert_called_once_with(
        RoleArn="arn:aws:iam::123456789012:role/CloudMonitor",
        RoleSessionName="cloud-security-monitor",
        ExternalId="tenant-external-id",
    )
    session_factory.assert_called_once_with(
        aws_access_key_id="temporary-access-key",
        aws_secret_access_key="temporary-secret-key",
        aws_session_token="temporary-session-token",
        region_name="ap-south-1",
    )


def test_ec2_collector_uses_supplied_session_not_platform_default():
    assumed_session = MagicMock()
    assumed_session.region_name = "eu-west-1"
    ec2_client = assumed_session.client.return_value
    paginator = ec2_client.get_paginator.return_value
    paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-tenant",
                            "State": {"Name": "running"},
                            "Tags": [{"Key": "Name", "Value": "tenant-instance"}],
                        }
                    ]
                }
            ]
        }
    ]

    with patch("app.collectors.aws.ec2.get_aws_session") as default_session:
        result = collect_ec2_instances(session=assumed_session)

    default_session.assert_not_called()
    assumed_session.client.assert_called_once_with("ec2")
    assert result == [
        {
            "asset_type": "ec2_instance",
            "asset_id": "i-tenant",
            "name": "tenant-instance",
            "region": "eu-west-1",
            "state": "running",
            "instance_type": None,
            "private_ip": None,
            "public_ip": None,
        }
    ]


def test_ec2_collector_preserves_default_session_compatibility():
    default_session = MagicMock()
    default_session.region_name = "us-east-1"
    paginator = (
        default_session.client.return_value
        .get_paginator.return_value
    )
    paginator.paginate.return_value = []

    with patch(
        "app.collectors.aws.ec2.get_aws_session",
        return_value=default_session,
    ) as get_default_session:
        result = collect_ec2_instances()

    assert result == []
    get_default_session.assert_called_once_with()
    default_session.client.assert_called_once_with("ec2")


def test_ec2_ingestion_collects_only_after_matching_assumed_identity():
    db = MagicMock()
    account = SimpleNamespace(
        id=41,
        account_id="123456789012",
        role_arn="arn:aws:iam::123456789012:role/CloudMonitor",
        region="ap-south-1",
        external_id="tenant-external-id",
    )
    assumed_session = MagicMock()
    stored_asset = MagicMock()

    with patch(
        "app.services.aws_ingestion_service.CloudAccountRepository.get_by_id",
        return_value=account,
    ) as get_account, patch(
        "app.services.aws_ingestion_service.assume_role_session",
        return_value=assumed_session,
    ) as assume, patch(
        "app.services.aws_ingestion_service.get_session_identity",
        return_value={
            "user_id": "role-session",
            "account_id": "123456789012",
            "arn": "arn:aws:sts::123456789012:assumed-role/CloudMonitor/session",
        },
    ) as identity, patch(
        "app.services.aws_ingestion_service.collect_ec2_instances",
        return_value=[
            {
                "asset_type": "ec2_instance",
                "asset_id": "i-tenant",
                "name": "tenant-instance",
                "region": "ap-south-1",
                "state": "running",
                "instance_type": "t3.micro",
                "private_ip": "10.0.0.10",
                "public_ip": "203.0.113.10",
            }
        ],
    ) as collect, patch(
        "app.services.aws_ingestion_service.AssetRepository.create_or_update",
        return_value=stored_asset,
    ) as store:
        result = AWSIngestionService.ingest_ec2_instances(
            db,
            cloud_account_id=41,
            organization_id=7,
        )

    assert result == {"collected": 1, "stored": 1}
    get_account.assert_called_once_with(db, 41, 7)
    assume.assert_called_once_with(
        account.role_arn,
        "ap-south-1",
        "tenant-external-id",
    )
    identity.assert_called_once_with(assumed_session)
    collect.assert_called_once_with(session=assumed_session)
    store.assert_called_once_with(
        db=db,
        cloud_account_id=41,
        organization_id=7,
        asset_type="ec2_instance",
        asset_id="i-tenant",
        name="tenant-instance",
        region="ap-south-1",
        resource_state="running",
        public_exposure=True,
        tags={
            "instance_type": "t3.micro",
            "private_ip": "10.0.0.10",
            "public_ip": "203.0.113.10",
        },
    )


def test_ec2_ingestion_rejects_mismatched_assumed_account_before_collection():
    db = MagicMock()
    account = SimpleNamespace(
        id=41,
        account_id="123456789012",
        role_arn="arn:aws:iam::123456789012:role/CloudMonitor",
        region="ap-south-1",
        external_id="tenant-external-id",
    )

    with patch(
        "app.services.aws_ingestion_service.CloudAccountRepository.get_by_id",
        return_value=account,
    ), patch(
        "app.services.aws_ingestion_service.assume_role_session",
        return_value=MagicMock(),
    ), patch(
        "app.services.aws_ingestion_service.get_session_identity",
        return_value={
            "user_id": "wrong-role-session",
            "account_id": "999999999999",
            "arn": "arn:aws:sts::999999999999:assumed-role/Wrong/session",
        },
    ), patch(
        "app.services.aws_ingestion_service.collect_ec2_instances",
    ) as collect, patch(
        "app.services.aws_ingestion_service.AssetRepository.create_or_update",
    ) as store:
        with pytest.raises(
            RuntimeError,
            match="Assumed role belongs to a different AWS account",
        ):
            AWSIngestionService.ingest_ec2_instances(
                db,
                cloud_account_id=41,
                organization_id=7,
            )

    collect.assert_not_called()
    store.assert_not_called()
