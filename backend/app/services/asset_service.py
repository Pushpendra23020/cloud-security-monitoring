from app.services.asset_risk_service import AssetRiskService
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate
from app.services.asset_risk_service import (
    AssetRiskService,
)

class AssetService:

    @staticmethod
    def create_asset(
        db: Session,
        asset_data: AssetCreate,
    ) -> Asset:

        existing_asset = AssetRepository.get_by_asset_id(
            db=db,
            asset_id=asset_data.asset_id,
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
    ) -> list[Asset]:

        return AssetRepository.get_all(db=db)
    
    @staticmethod
    def enrich_all_assets(
        db: Session,
    ) -> list[Asset]:

        assets = AssetRepository.get_all(
            db=db
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
