from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.asset import Asset
from app.schemas.asset import AssetCreate


class AssetRepository:

    @staticmethod
    def get_by_asset_id(
        db: Session,
        asset_id: str,
    ) -> Asset | None:
        statement = select(
            Asset
        ).where(
            Asset.asset_id == asset_id
        )

        return db.scalar(statement)

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Asset]:
        statement = select(
            Asset
        ).order_by(
            Asset.created_at.desc()
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def create(
        db: Session,
        asset_data: AssetCreate,
    ) -> Asset:
        asset = Asset(
            cloud_account_id=(
                asset_data.cloud_account_id
            ),
            asset_type=asset_data.asset_type,
            asset_id=asset_data.asset_id,
            name=asset_data.name,
            region=asset_data.region,

            risk_score=(
                asset_data.risk_score
            ),
            risk_level=(
                asset_data.risk_level
            ),
            findings_count=(
                asset_data.findings_count
            ),
            alerts_count=(
                asset_data.alerts_count
            ),
            public_exposure=(
                asset_data.public_exposure
            ),
            resource_state=(
                asset_data.resource_state
            ),
            tags=asset_data.tags,
            last_seen=asset_data.last_seen,
        )

        db.add(asset)
        db.commit()
        db.refresh(asset)

        return asset

    @staticmethod
     
    def create_or_update(
        db: Session,
        *,
        cloud_account_id: int,
        asset_type: str,
        asset_id: str,
        name: str | None = None,
        region: str | None = None,
        resource_state: str | None = None,
        public_exposure: bool | None = None,
        tags: dict | None = None,
        last_seen: datetime | None = None,
    ) -> Asset:

        asset = (
            AssetRepository.get_by_asset_id(
                db=db,
                asset_id=asset_id,
            )
        )

        if asset is None:
            asset = Asset(
                cloud_account_id=cloud_account_id,
                asset_type=asset_type,
                asset_id=asset_id,
                name=name,
                region=region,

                resource_state=(
                    resource_state
                    if resource_state is not None
                    else "unknown"
                ),

                public_exposure=(
                    public_exposure
                    if public_exposure is not None
                    else False
                ),

                tags=(
                    tags
                    if tags is not None
                    else {}
                ),

                last_seen=last_seen,
            )

            db.add(asset)

        else:
            asset.cloud_account_id = (
                cloud_account_id
            )

            asset.asset_type = asset_type

            if name is not None:
                asset.name = name

            if region is not None:
                asset.region = region

            if resource_state is not None:
                asset.resource_state = (
                    resource_state
                )

            if public_exposure is not None:
                asset.public_exposure = (
                    public_exposure
                )

            if tags is not None:
                merged_tags = dict(
                    asset.tags or {}
                )

                merged_tags.update(tags)

                asset.tags = merged_tags

            if last_seen is not None:
                asset.last_seen = last_seen

        db.commit()
        db.refresh(asset)

        return asset
    @staticmethod
    def get_risk_refresh_batch(
        db: Session,
        *,
        stale_before: datetime,
        batch_size: int = 100,
        after_id: int = 0,
    ) -> list[Asset]:
        statement = (
            select(Asset)
            .where(
                Asset.id > after_id,
                or_(
                    Asset.risk_updated_at.is_(None),
                    Asset.risk_updated_at
                    < stale_before,
                ),
            )
            .order_by(Asset.id.asc())
            .limit(batch_size)
        )

        return list(
            db.scalars(
                statement
            ).all()
        )
