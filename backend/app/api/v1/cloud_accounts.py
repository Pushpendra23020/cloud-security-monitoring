from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.user import User
from app.dependencies import require_roles
from app.schemas.cloud_account import (
    CloudAccountCreate,
    CloudAccountResponse,
    CloudAccountUpdate,
    CloudAccountConnectionResponse,
)
from app.services.cloud_account_service import CloudAccountService


router = APIRouter(
    prefix="/cloud-accounts",
    tags=["Cloud Accounts"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_roles("admin"))]


@router.post(
    "",
    response_model=CloudAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cloud_account(
    account_data: CloudAccountCreate,
    db: DatabaseSession,
    _: AdminUser,
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


@router.patch("/{account_id}", response_model=CloudAccountResponse)
def update_cloud_account(account_id: int, account_data: CloudAccountUpdate, db: DatabaseSession, _: AdminUser):
    return CloudAccountService.update_cloud_account(db, account_id, account_data)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cloud_account(account_id: int, db: DatabaseSession, _: AdminUser) -> None:
    CloudAccountService.delete_cloud_account(db, account_id)


@router.post("/{account_id}/test-connection", response_model=CloudAccountConnectionResponse)
def test_cloud_account_connection(account_id: int, db: DatabaseSession, _: AdminUser):
    return CloudAccountService.test_connection(db, account_id)
