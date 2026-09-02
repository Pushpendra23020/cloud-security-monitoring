from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models.security_event import SecurityEventRecord
from app.models.security_event import SecurityEvent
from app.normalizers.aws.cloudtrail import normalize_cloudtrail_event
from app.pipeline.event_classifier import classify_event
from app.pipeline.event_validator import validate_event


class EventQueueRepository:
    def __init__(self, session: Session, organization_id: int):
        self.session = session
        self.organization_id = organization_id

    @staticmethod
    def normalize(raw_event: dict[str, Any]) -> SecurityEvent:
        return classify_event(validate_event(normalize_cloudtrail_event(raw_event)))

    def enqueue(
        self,
        raw_event: dict[str, Any],
        *,
        source: str = "cloudtrail",
        max_attempts: int = 5,
    ) -> tuple[bool, SecurityEvent]:
        event = self.normalize(raw_event)
        record = SecurityEventRecord(
            organization_id=self.organization_id,
            event_id=event.event_id,
            source=source,
            raw_event=raw_event,
            normalized_event=event.model_dump(mode="json"),
            status="queued",
            max_attempts=max_attempts,
        )
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False, event
        return True, event

    def enqueue_batch(
        self,
        raw_events: Iterable[dict[str, Any]],
        *,
        source: str = "cloudtrail",
        max_attempts: int = 5,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "processed": 0,
            "saved": 0,
            "duplicates": 0,
            "failed": 0,
            "errors": [],
        }
        for index, raw_event in enumerate(raw_events):
            result["processed"] += 1
            try:
                saved, _event = self.enqueue(
                    raw_event,
                    source=source,
                    max_attempts=max_attempts,
                )
                if saved:
                    result["saved"] += 1
                else:
                    result["duplicates"] += 1
            except Exception as exc:
                self.session.rollback()
                result["failed"] += 1
                result["errors"].append(
                    {
                        "index": index,
                        "event_id": raw_event.get("eventID"),
                        "event_name": raw_event.get("eventName"),
                        "error": str(exc),
                    }
                )
        return result

    def claim_batch(
        self,
        *,
        worker_id: str,
        batch_size: int,
        lock_timeout_seconds: int,
    ) -> list[SecurityEventRecord]:
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=lock_timeout_seconds)

        self.session.execute(
            update(SecurityEventRecord)
            .where(
                SecurityEventRecord.organization_id == self.organization_id,
                SecurityEventRecord.status == "processing",
                SecurityEventRecord.locked_at < stale_before,
                SecurityEventRecord.attempts >= SecurityEventRecord.max_attempts,
            )
            .values(
                status="dead_letter",
                locked_at=None,
                locked_by=None,
                last_error="Worker lease expired after the final attempt.",
            )
        )
        self.session.execute(
            update(SecurityEventRecord)
            .where(
                SecurityEventRecord.organization_id == self.organization_id,
                SecurityEventRecord.status == "processing",
                SecurityEventRecord.locked_at < stale_before,
                SecurityEventRecord.attempts < SecurityEventRecord.max_attempts,
            )
            .values(
                status="retry",
                available_at=now,
                locked_at=None,
                locked_by=None,
                last_error="Worker lease expired; event returned to the queue.",
            )
        )

        statement = (
            select(SecurityEventRecord)
            .where(
                SecurityEventRecord.organization_id == self.organization_id,
                SecurityEventRecord.status.in_(("queued", "retry")),
                SecurityEventRecord.available_at <= now,
                SecurityEventRecord.attempts < SecurityEventRecord.max_attempts,
            )
            .order_by(
                SecurityEventRecord.available_at,
                SecurityEventRecord.received_at,
                SecurityEventRecord.id,
            )
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        records = list(self.session.scalars(statement))
        for record in records:
            record.status = "processing"
            record.attempts += 1
            record.locked_at = now
            record.locked_by = worker_id
            record.last_error = None
        self.session.commit()
        return records

    def mark_completed(self, record_id: int) -> None:
        record = self._get(record_id)
        if record is None:
            return
        record.status = "completed"
        record.processed_at = datetime.now(timezone.utc)
        record.locked_at = None
        record.locked_by = None
        record.last_error = None
        self.session.commit()

    def mark_archived(
        self,
        record_id: int,
        *,
        uri: str,
        sha256: str,
        archived_at: datetime,
        retention_until: datetime | None,
    ) -> None:
        record = self._get(record_id)
        if record is None:
            return
        record.archive_uri = uri
        record.archive_sha256 = sha256
        record.archived_at = archived_at
        record.archive_retention_until = retention_until
        self.session.commit()

    def mark_failed(self, record_id: int, error: Exception, *, base_delay: int) -> str:
        record = self._get(record_id)
        if record is None:
            return "missing"
        record.last_error = str(error)[:4000]
        record.locked_at = None
        record.locked_by = None
        if record.attempts >= record.max_attempts:
            record.status = "dead_letter"
        else:
            record.status = "retry"
            delay = base_delay * (2 ** max(record.attempts - 1, 0))
            record.available_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        self.session.commit()
        return record.status

    def replay_dead_letter(self, record_id: int) -> bool:
        record = self._get(record_id)
        if record is None or record.status != "dead_letter":
            return False
        record.status = "queued"
        record.attempts = 0
        record.available_at = datetime.now(timezone.utc)
        record.locked_at = None
        record.locked_by = None
        record.last_error = None
        record.processed_at = None
        self.session.commit()
        return True

    def counts(self) -> dict[str, int]:
        rows = self.session.execute(
            select(SecurityEventRecord.status, func.count(SecurityEventRecord.id))
            .where(SecurityEventRecord.organization_id == self.organization_id)
            .group_by(SecurityEventRecord.status)
        ).all()
        return {status: count for status, count in rows}

    def health(self, *, alert_age_seconds: int) -> dict[str, Any]:
        counts = self.counts()
        oldest = self.session.scalar(
            select(func.min(SecurityEventRecord.received_at)).where(
                SecurityEventRecord.organization_id == self.organization_id,
                SecurityEventRecord.status.in_(("queued", "processing", "retry")),
            )
        )
        oldest_age = 0
        if oldest is not None:
            oldest_age = max(
                int((datetime.now(timezone.utc) - oldest).total_seconds()),
                0,
            )
        return {
            **counts,
            "oldest_pending_age_seconds": oldest_age,
            "healthy": counts.get("dead_letter", 0) == 0
            and oldest_age <= alert_age_seconds,
        }

    def list_dead_letters(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[SecurityEventRecord], int]:
        filters = (
            SecurityEventRecord.organization_id == self.organization_id,
            SecurityEventRecord.status == "dead_letter",
        )
        total = int(
            self.session.scalar(
                select(func.count(SecurityEventRecord.id)).where(*filters)
            )
            or 0
        )
        records = list(
            self.session.scalars(
                select(SecurityEventRecord)
                .where(*filters)
                .order_by(SecurityEventRecord.received_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return records, total

    def purge_archived_completed(
        self,
        *,
        retention_days: int,
        batch_size: int,
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        record_ids = list(
            self.session.scalars(
                select(SecurityEventRecord.id)
                .where(
                    SecurityEventRecord.organization_id == self.organization_id,
                    SecurityEventRecord.status == "completed",
                    SecurityEventRecord.processed_at < cutoff,
                    SecurityEventRecord.archived_at.is_not(None),
                    SecurityEventRecord.archive_uri.is_not(None),
                )
                .order_by(SecurityEventRecord.processed_at, SecurityEventRecord.id)
                .limit(batch_size)
            )
        )
        if record_ids:
            self.session.execute(
                delete(SecurityEventRecord).where(
                    SecurityEventRecord.organization_id == self.organization_id,
                    SecurityEventRecord.id.in_(record_ids),
                )
            )
            self.session.commit()
        return len(record_ids)

    def _get(self, record_id: int) -> SecurityEventRecord | None:
        return self.session.scalar(
            select(SecurityEventRecord).where(
                SecurityEventRecord.id == record_id,
                SecurityEventRecord.organization_id == self.organization_id,
            )
        )
