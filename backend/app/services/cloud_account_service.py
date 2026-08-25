from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.cloud_account import CloudAccount
from app.repositories.cloud_account_repository import (
    CloudAccountRepository,
)
from app.collectors.aws.sts import AWSConnectionError, assume_role_identity
from app.schemas.cloud_account import CloudAccountCreate, CloudAccountUpdate


class CloudAccountService:
    @staticmethod
    def get_account(db: Session, account_id: int) -> CloudAccount:
        account = CloudAccountRepository.get_by_id(db, account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="Cloud account not found.")
        return account

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

    @staticmethod
    def update_cloud_account(db: Session, account_id: int, data: CloudAccountUpdate) -> CloudAccount:
        return CloudAccountRepository.update(db, CloudAccountService.get_account(db, account_id), data)

    @staticmethod
    def delete_cloud_account(db: Session, account_id: int) -> None:
        CloudAccountRepository.delete(db, CloudAccountService.get_account(db, account_id))

    @staticmethod
    def test_connection(db: Session, account_id: int) -> dict:
        account = CloudAccountService.get_account(db, account_id)
        if not account.role_arn:
            raise HTTPException(status_code=422, detail="A monitoring role ARN is required.")
        try:
            identity = assume_role_identity(account.role_arn, account.region or "us-east-1", account.external_id)
        except AWSConnectionError as exc:
            account.health_status = "failed"
            db.commit()
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if identity["account_id"] != account.account_id:
            account.health_status = "failed"
            db.commit()
            raise HTTPException(status_code=409, detail="Assumed role belongs to a different AWS account.")
        account.health_status = "healthy"
        db.commit()
        return {
            "success": True,
            "account_id": identity["account_id"],
            "region": account.region or "us-east-1",
            "role_arn": account.role_arn,
            "permissions": {service: True for service in account.services},
            "message": "STS AssumeRole connection succeeded.",
        }
