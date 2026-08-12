from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.asset import Asset


class AssetRepository:

    @staticmethod
    def get_by_asset_id(
        db: Session,
        asset_id: str,
    ) -> Asset | None:

        statement = select(Asset).where(
            Asset.asset_id == asset_id
        )

        return db.scalar(statement)

    @staticmethod
    def create_or_update(
        db: Session,
        *,
        cloud_account_id: int,
        asset_type: str,
        asset_id: str,
        name: str | None,
        region: str | None,
    ) -> Asset:

        asset = AssetRepository.get_by_asset_id(
            db=db,
            asset_id=asset_id,
        )

        if asset is None:
            asset = Asset(
                cloud_account_id=cloud_account_id,
                asset_type=asset_type,
                asset_id=asset_id,
                name=name,
                region=region,
            )

            db.add(asset)

        else:
            asset.cloud_account_id = cloud_account_id
            asset.asset_type = asset_type
            asset.name = name
            asset.region = region

        db.commit()
        db.refresh(asset)

        return asset
