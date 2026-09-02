import argparse
import json
import logging

from app.collectors.aws.cloudtrail import (
    CloudTrailCollector,
)
from app.collectors.aws.sts import assume_role_session, get_session_identity
from app.database.session import SessionLocal, set_tenant_context
from app.repositories.cloud_account_repository import CloudAccountRepository
from app.repositories.event_queue_repository import EventQueueRepository
from app.services.cloudtrail_ingestion_service import (
    CloudTrailIngestionService,
)
from app.storage.checkpoint_store import (
    CheckpointStore,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Collect and ingest AWS "
            "CloudTrail events."
        )
    )

    parser.add_argument("--organization-id", type=int, required=True)
    parser.add_argument("--cloud-account-id", type=int, required=True)

    parser.add_argument(
        "--region",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    db = SessionLocal()
    set_tenant_context(db, args.organization_id)
    account = CloudAccountRepository.get_by_id(
        db,
        args.cloud_account_id,
        args.organization_id,
    )
    if account is None:
        raise SystemExit("Cloud account not found in the requested organization.")
    if not account.role_arn:
        raise SystemExit("Cloud account does not have a monitoring role ARN.")

    region = args.region or account.region or "us-east-1"
    session = assume_role_session(account.role_arn, region, account.external_id)
    identity = get_session_identity(session)
    account_id = identity["account_id"]
    if account_id != account.account_id:
        raise SystemExit("Assumed role belongs to a different AWS account.")

    logging.info(
        (
            "aws_identity_resolved "
            "account_id=%s region=%s"
        ),
        account_id,
        region,
    )

    cloudtrail_client = session.client(
        "cloudtrail"
    )

    collector = CloudTrailCollector(
        client=cloudtrail_client
    )

    checkpoint_store = (
        CheckpointStore.for_cloudtrail(
            account_id=account_id,
            region=region,
            organization_id=args.organization_id,
        )
    )

    service = CloudTrailIngestionService(
        collector=collector,
        organization_id=args.organization_id,
        checkpoint_store=checkpoint_store,
        queue_repository=EventQueueRepository(
            db,
            args.organization_id,
        ),
    )

    result = service.collect_and_ingest(
        lookback_minutes=(
            args.lookback_minutes
        )
    )

    output = {
        "account_id": account_id,
        "region": region,
        "organization_id": args.organization_id,
        **result,
    }

    print(
        json.dumps(
            output,
            indent=2,
        )
    )
    db.close()


if __name__ == "__main__":
    main()
