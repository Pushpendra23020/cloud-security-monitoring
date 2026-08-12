from sqlalchemy.orm import Session

from app.collectors.aws.ec2 import (
    EC2CollectorError,
    collect_ec2_instances,
)
from app.repositories.asset_repository import AssetRepository


class AWSIngestionService:

    @staticmethod
    def ingest_ec2_instances(
        db: Session,
        cloud_account_id: int,
    ) -> dict:

        try:
            instances = collect_ec2_instances()

            stored_assets = []

            for instance in instances:

                asset = AssetRepository.create_or_update(
                    db=db,
                    cloud_account_id=cloud_account_id,
                    asset_type=instance["asset_type"],
                    asset_id=instance["asset_id"],
                    name=instance.get("name"),
                    region=instance.get("region"),
                )

                stored_assets.append(asset)

            return {
                "collected": len(instances),
                "stored": len(stored_assets),
            }

        except EC2CollectorError as exc:
            raise RuntimeError(
                f"EC2 ingestion failed: {exc}"
            ) from exc
