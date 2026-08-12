from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.cloud_account import CloudAccount
from app.schemas.cloud_account import CloudAccountCreate


class CloudAccountRepository:
    @staticmethod
    def create(
        db: Session,
        account_data: CloudAccountCreate,
    ) -> CloudAccount:
        cloud_account = CloudAccount(
            provider=account_data.provider.lower(),
            account_id=account_data.account_id,
            region=account_data.region,
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
