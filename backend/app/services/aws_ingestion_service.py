from sqlalchemy.orm import Session

from app.collectors.aws.ec2 import (
    EC2CollectorError,
    collect_ec2_instances,
)
from app.collectors.aws.sts import (
    AWSConnectionError,
    assume_role_session,
    get_session_identity,
)
from app.repositories.asset_repository import AssetRepository
from app.repositories.cloud_account_repository import CloudAccountRepository
from app.core.tenancy import DEFAULT_ORGANIZATION_ID


class AWSIngestionService:

    @staticmethod
    def ingest_ec2_instances(
        db: Session,
        cloud_account_id: int,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> dict:

        cloud_account = CloudAccountRepository.get_by_id(
            db,
            cloud_account_id,
            organization_id,
        )
        if cloud_account is None:
            raise RuntimeError("Cloud account not found.")
        if not cloud_account.role_arn:
            raise RuntimeError("A monitoring role ARN is required for EC2 collection.")

        try:
            aws_session = assume_role_session(
                cloud_account.role_arn,
                cloud_account.region or "us-east-1",
                cloud_account.external_id,
            )
            identity = get_session_identity(aws_session)
            if identity["account_id"] != cloud_account.account_id:
                raise RuntimeError(
                    "Assumed role belongs to a different AWS account."
                )

            instances = collect_ec2_instances(
                session=aws_session,
            )

            stored_assets = []

            for instance in instances:

                asset = AssetRepository.create_or_update(
                    db=db,
                    cloud_account_id=cloud_account.id,
                    organization_id=organization_id,
                    asset_type=instance["asset_type"],
                    asset_id=instance["asset_id"],
                    name=instance.get("name"),
                    region=instance.get("region"),
                    resource_state=instance.get("state"),
                    public_exposure=bool(instance.get("public_ip")),
                    tags={
                        "instance_type": instance.get("instance_type"),
                        "private_ip": instance.get("private_ip"),
                        "public_ip": instance.get("public_ip"),
                    },
                )

                stored_assets.append(asset)

            return {
                "collected": len(instances),
                "stored": len(stored_assets),
            }

        except (AWSConnectionError, EC2CollectorError) as exc:
            raise RuntimeError(
                f"EC2 ingestion failed: {exc}"
            ) from exc
