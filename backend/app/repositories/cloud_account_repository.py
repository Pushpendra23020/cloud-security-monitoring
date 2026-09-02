from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.cloud_account import CloudAccount
from app.schemas.cloud_account import CloudAccountCreate, CloudAccountUpdate
from app.core.tenancy import DEFAULT_ORGANIZATION_ID


class CloudAccountRepository:
    @staticmethod
    def create(
        db: Session,
        account_data: CloudAccountCreate,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> CloudAccount:
        cloud_account = CloudAccount(
            organization_id=organization_id,
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
    def get_all(db: Session, organization_id: int = DEFAULT_ORGANIZATION_ID) -> list[CloudAccount]:
        statement = select(CloudAccount).where(
            CloudAccount.organization_id == organization_id
        ).order_by(
            CloudAccount.created_at.desc()
        )

        return list(db.scalars(statement).all())

    @staticmethod
    def get_by_account_id(
        db: Session,
        account_id: str,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> CloudAccount | None:
        statement = select(CloudAccount).where(
            CloudAccount.account_id == account_id
            , CloudAccount.organization_id == organization_id
        )

        return db.scalar(statement)

    @staticmethod
    def get_by_id(
        db: Session,
        account_id: int,
        organization_id: int = DEFAULT_ORGANIZATION_ID,
    ) -> CloudAccount | None:
        return db.scalar(
            select(CloudAccount).where(
                CloudAccount.id == account_id,
                CloudAccount.organization_id == organization_id,
            )
        )

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
