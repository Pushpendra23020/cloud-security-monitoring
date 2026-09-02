from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.tenancy import DEFAULT_ORGANIZATION_ID
from app.database.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.cloud_account_repository import CloudAccountRepository
from app.schemas.asset import AssetCreate
from app.services.asset_risk_service import (
    AssetRiskService,
)


class AssetService:

    @staticmethod
    def create_asset(
        db: Session,
        asset_data: AssetCreate,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> Asset:
        cloud_account = CloudAccountRepository.get_by_id(
            db=db,
            account_id=asset_data.cloud_account_id,
            organization_id=organization_id,
        )

        if cloud_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cloud account not found.",
            )

        existing_asset = AssetRepository.get_by_asset_id(
            db=db,
            asset_id=asset_data.asset_id,
            organization_id=organization_id,
        )

        if existing_asset is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset already exists.",
            )

        try:
            return AssetRepository.create(
                db=db,
                asset_data=asset_data,
                organization_id=organization_id,
            )

        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset already exists.",
            ) from exc

    @staticmethod
    def list_assets(
        db: Session,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> list[Asset]:

        return AssetRepository.get_all(
            db=db,
            organization_id=organization_id,
        )

    @staticmethod
    def enrich_all_assets(
        db: Session,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> list[Asset]:

        assets = AssetRepository.get_all(
            db=db,
            organization_id=organization_id,
        )

        enriched_assets = []

        for asset in assets:
            enriched_assets.append(
                AssetRiskService.enrich_asset(
                    db=db,
                    asset=asset,
                )
            )
        return enriched_assets
