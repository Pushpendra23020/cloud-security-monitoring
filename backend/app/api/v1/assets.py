from typing import Annotated

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
    "",
    response_model=list[AssetResponse],
)
def list_assets(
    db: DatabaseSession,
) -> list[AssetResponse]:

    return AssetService.list_assets(db=db)

