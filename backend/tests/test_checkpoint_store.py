from datetime import datetime, timezone

from app.storage.checkpoint_store import CheckpointStore


def test_checkpoint_can_be_saved_and_loaded(tmp_path):
    checkpoint_file = tmp_path / "checkpoint.json"

    store = CheckpointStore(str(checkpoint_file))

    timestamp = datetime(
        2026,
        8,
        12,
        10,
        0,
        tzinfo=timezone.utc,
    )

    store.save_checkpoint(timestamp)

    loaded = store.get_last_checkpoint()

    assert loaded == timestamp


def test_missing_checkpoint_returns_none(tmp_path):
    checkpoint_file = tmp_path / "checkpoint.json"

    store = CheckpointStore(str(checkpoint_file))

    assert store.get_last_checkpoint() is None
