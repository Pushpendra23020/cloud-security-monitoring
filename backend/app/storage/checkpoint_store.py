import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class CheckpointStore:
    def __init__(
        self,
        file_path: str = "data/checkpoints/cloudtrail.json",
    ):
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    @classmethod
    def for_cloudtrail(
        cls,
        account_id: str,
        region: str,
        base_dir: str = "data/checkpoints",
    ):
        file_path = (
            Path(base_dir)
            / "aws"
            / account_id
            / f"{region}.json"
        )

        return cls(str(file_path))

    def get_last_checkpoint(
        self,
    ) -> Optional[datetime]:

        if not self.file_path.exists():
            return None

        with self.file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        value = data.get(
            "last_successful_collection"
        )

        if not value:
            return None

        return datetime.fromisoformat(value)

    def save_checkpoint(
        self,
        timestamp: datetime,
    ) -> None:

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        payload = {
            "last_successful_collection":
                timestamp.isoformat()
        }

        temp_file = self.file_path.with_suffix(
            ".tmp"
        )

        with temp_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                indent=2,
            )

        temp_file.replace(
            self.file_path
        )
