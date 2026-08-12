from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.cloud_account import CloudAccount
from app.repositories.cloud_account_repository import (
    CloudAccountRepository,
)
from app.schemas.cloud_account import CloudAccountCreate


class CloudAccountService:
    @staticmethod
    def create_cloud_account(
        db: Session,
        account_data: CloudAccountCreate,
    ) -> CloudAccount:
        existing_account = CloudAccountRepository.get_by_account_id(
            db=db,
            account_id=account_data.account_id,
        )

        if existing_account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cloud account already exists.",
            )

        try:
            return CloudAccountRepository.create(
                db=db,
                account_data=account_data,
            )
        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cloud account already exists.",
            ) from exc

    @staticmethod
    def list_cloud_accounts(
        db: Session,
    ) -> list[CloudAccount]:
        return CloudAccountRepository.get_all(db=db)
