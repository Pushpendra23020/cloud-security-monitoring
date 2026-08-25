from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.cloud_account import CloudAccount
from app.schemas.cloud_account import CloudAccountCreate, CloudAccountUpdate


class CloudAccountRepository:
    @staticmethod
    def create(
        db: Session,
        account_data: CloudAccountCreate,
    ) -> CloudAccount:
        cloud_account = CloudAccount(
            name=account_data.name,
            provider=account_data.provider.lower(),
            account_id=account_data.account_id,
            region=account_data.region,
            auth_method=account_data.auth_method,
            role_arn=account_data.role_arn,
            external_id=account_data.external_id,
            monitoring_enabled=account_data.monitoring_enabled,
            services=account_data.services,
            description=account_data.description,
        )

        db.add(cloud_account)
        db.commit()
        db.refresh(cloud_account)

        return cloud_account

    @staticmethod
    def get_all(db: Session) -> list[CloudAccount]:
        statement = select(CloudAccount).order_by(
            CloudAccount.created_at.desc()
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_by_account_id(
        db: Session,
        account_id: str,
    ) -> CloudAccount | None:
        statement = select(CloudAccount).where(
            CloudAccount.account_id == account_id
        )

        return db.scalar(statement)

    @staticmethod
    def get_by_id(db: Session, account_id: int) -> CloudAccount | None:
        return db.get(CloudAccount, account_id)

    @staticmethod
    def update(db: Session, account: CloudAccount, data: CloudAccountUpdate) -> CloudAccount:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def delete(db: Session, account: CloudAccount) -> None:
        db.delete(account)
        db.commit()
