from app.services.asset_metadata_enricher import (
    AssetMetadataEnricher,
)
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.asset import Asset
from app.database.models.cloud_account import (
    CloudAccount,
)
from app.models.security_event import (
    SecurityEvent,
)
from app.repositories.asset_repository import (
    AssetRepository,
)


class AssetDiscoveryService:

    @staticmethod
    def get_cloud_account(
        db: Session,
        *,
        provider: str,
        account_id: str,
    ) -> CloudAccount | None:

        statement = select(
            CloudAccount
        ).where(
            CloudAccount.provider == provider,
            CloudAccount.account_id
            == account_id,
        )

        return db.scalar(statement)

    @staticmethod
    def infer_resource_state(
        event: SecurityEvent,
    ) -> str:

        event_name = (
            event.event_name or ""
        ).lower()

        state_map = {
            "runinstances": "running",
            "startinstances": "running",
            "stopinstances": "stopped",
            "terminateinstances": "terminated",
        }

        return state_map.get(
            event_name,
            "unknown",
        )

    @classmethod
    def discover_from_event(
        cls,
        db: Session,
        event: SecurityEvent,
    ) -> Asset | None:

        if not event.resource_id:
            return None

        if not event.resource_type:
            return None

        if not event.account_id:
            return None

        cloud_account = (
            cls.get_cloud_account(
                db=db,
                provider=event.cloud_provider,
                account_id=event.account_id,
            )
        )

        if cloud_account is None:
            return None

        metadata = (
        AssetMetadataEnricher.enrich(
        event
       )
       ) 
        return (
        AssetRepository.create_or_update(
        db=db,

        cloud_account_id=(
            cloud_account.id
        ),

        asset_type=(
            event.resource_type
        ),

        asset_id=(
            event.resource_id
        ),

        name=metadata["name"],

        region=event.region,

        resource_state=(
            metadata[
                "resource_state"
            ]
        ),

        public_exposure=(
            metadata[
                "public_exposure"
            ]
        ),

        tags=metadata["tags"],

        last_seen=datetime.now(
            timezone.utc
        ),
    )
)
