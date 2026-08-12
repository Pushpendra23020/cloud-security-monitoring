from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.cloud_account import (
    CloudAccountCreate,
    CloudAccountResponse,
)
from app.services.cloud_account_service import CloudAccountService


router = APIRouter(
    prefix="/cloud-accounts",
    tags=["Cloud Accounts"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=CloudAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cloud_account(
    account_data: CloudAccountCreate,
    db: DatabaseSession,
) -> CloudAccountResponse:
    return CloudAccountService.create_cloud_account(
        db=db,
        account_data=account_data,
    )


@router.get(
    "",
    response_model=list[CloudAccountResponse],
)
def list_cloud_accounts(
    db: DatabaseSession,
) -> list[CloudAccountResponse]:
    return CloudAccountService.list_cloud_accounts(db=db)
