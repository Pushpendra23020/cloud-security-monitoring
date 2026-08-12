import argparse
import json
import logging

from app.collectors.aws.client_factory import (
    create_aws_session,
)
from app.collectors.aws.cloudtrail import (
    CloudTrailCollector,
)
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

    parser.add_argument(
        "--profile",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
    )

    parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    session = create_aws_session(
        profile_name=args.profile,
        region_name=args.region,
    )

    sts_client = session.client(
        "sts"
    )

    identity = (
        sts_client.get_caller_identity()
    )

    account_id = identity["Account"]

    logging.info(
        (
            "aws_identity_resolved "
            "account_id=%s region=%s"
        ),
        account_id,
        args.region,
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
            region=args.region,
        )
    )

    service = CloudTrailIngestionService(
        collector=collector,
        checkpoint_store=checkpoint_store,
    )

    result = service.collect_and_ingest(
        lookback_minutes=(
            args.lookback_minutes
        )
    )

    output = {
        "account_id": account_id,
        "region": args.region,
        **result,
    }

    print(
        json.dumps(
            output,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
