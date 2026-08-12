from datetime import (
    datetime,
    timezone,
)

from app.storage.checkpoint_store import (
    CheckpointStore,
)


def test_checkpoints_are_isolated_by_region(
    tmp_path,
):
    account_id = "123456789012"

    us_store = (
        CheckpointStore.for_cloudtrail(
            account_id=account_id,
            region="us-east-1",
            base_dir=str(tmp_path),
        )
    )

    ap_store = (
        CheckpointStore.for_cloudtrail(
            account_id=account_id,
            region="ap-south-1",
            base_dir=str(tmp_path),
        )
    )

    us_timestamp = datetime(
        2026,
        8,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    ap_timestamp = datetime(
        2026,
        8,
        12,
        10,
        30,
        tzinfo=timezone.utc,
    )

    us_store.save_checkpoint(
        us_timestamp
    )

    ap_store.save_checkpoint(
        ap_timestamp
    )

    assert (
        us_store.get_last_checkpoint()
        == us_timestamp
    )

    assert (
        ap_store.get_last_checkpoint()
        == ap_timestamp
    )

    assert (
        us_store.file_path
        != ap_store.file_path
    )


def test_checkpoints_are_isolated_by_account(
    tmp_path,
):
    first_store = (
        CheckpointStore.for_cloudtrail(
            account_id="111111111111",
            region="us-east-1",
            base_dir=str(tmp_path),
        )
    )

    second_store = (
        CheckpointStore.for_cloudtrail(
            account_id="222222222222",
            region="us-east-1",
            base_dir=str(tmp_path),
        )
    )

    assert (
        first_store.file_path
        != second_store.file_path
    )
