from typing import Annotated
from app.repositories.asset_repository import AssetRepository
from app.services.asset_risk_service import AssetRiskService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.asset import AssetCreate, AssetResponse
from app.services.asset_service import AssetService


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    asset_data: AssetCreate,
    db: DatabaseSession,
) -> AssetResponse:

    return AssetService.create_asset(
        db=db,
        asset_data=asset_data,
    )

@router.get(
    "/{asset_id}/risk-explanation",
    summary="Explain asset risk score",
)
def explain_asset_risk(
    asset_id: str,
    db: DatabaseSession,
):
    asset = AssetRepository.get_by_asset_id(
        db=db,
        asset_id=asset_id,
    )

    if asset is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return AssetRiskService.explain_asset_risk(
        db=db,
        asset=asset,
    )
def list_assets(
    db: DatabaseSession,
) -> list[AssetResponse]:

    return AssetService.list_assets(db=db)

@router.post(
    "/enrich",
    response_model=list[AssetResponse],
    summary="Recalculate asset security risk",
)
def enrich_assets(
    db: DatabaseSession,
) -> list[AssetResponse]:

    return AssetService.enrich_all_assets(
        db=db
    )
