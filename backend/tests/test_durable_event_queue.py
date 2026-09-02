from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.config import settings
from app.database.models.organization import Organization
from app.database.models.security_event import SecurityEventRecord
from app.database.session import SessionLocal, set_tenant_context
from app.repositories.event_queue_repository import EventQueueRepository
from app.workers.event_ingestion_worker import EventIngestionWorker
from app.services.event_archive_service import ArchiveResult


class StubArchive:
    def archive(self, record):
        now = datetime.now(timezone.utc)
        return ArchiveResult(
            uri=f"memory://{record.organization_id}/{record.event_id}",
            sha256="a" * 64,
            archived_at=now,
            retention_until=now,
        )


def build_event(event_id: str) -> dict:
    return {
        "eventVersion": "1.08",
        "userIdentity": {
            "type": "IAMUser",
            "accountId": "123456789012",
            "userName": "queue-test",
        },
        "eventTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "198.51.100.20",
        "eventID": event_id,
        "responseElements": {"ConsoleLogin": "Failure"},
    }


@pytest.fixture
def organization_id():
    suffix = uuid4().hex
    with SessionLocal() as db:
        organization = Organization(
            name=f"Queue Test {suffix}",
            slug=f"queue-test-{suffix}",
        )
        db.add(organization)
        db.commit()
        value = organization.id
    try:
        yield value
    finally:
        with SessionLocal() as db:
            db.execute(
                delete(SecurityEventRecord).where(
                    SecurityEventRecord.organization_id == value
                )
            )
            db.execute(delete(Organization).where(Organization.id == value))
            db.commit()


def test_enqueue_is_durable_and_tenant_idempotent(organization_id):
    event_id = f"queue-{uuid4().hex}"
    with SessionLocal() as db:
        set_tenant_context(db, organization_id)
        repository = EventQueueRepository(db, organization_id)
        saved, normalized = repository.enqueue(build_event(event_id))
        duplicate, _ = repository.enqueue(build_event(event_id))
        counts = repository.counts()

    assert saved is True
    assert normalized.event_id == event_id
    assert duplicate is False
    assert counts == {"queued": 1}


def test_claim_retry_dead_letter_and_replay(organization_id):
    event_id = f"retry-{uuid4().hex}"
    with SessionLocal() as db:
        set_tenant_context(db, organization_id)
        repository = EventQueueRepository(db, organization_id)
        saved, _ = repository.enqueue(build_event(event_id), max_attempts=1)
        assert saved is True
        claimed = repository.claim_batch(
            worker_id="retry-test-worker",
            batch_size=1,
            lock_timeout_seconds=60,
        )
        assert len(claimed) == 1
        assert claimed[0].attempts == 1
        record_id = claimed[0].id
        state = repository.mark_failed(
            record_id,
            RuntimeError("simulated processing failure"),
            base_delay=1,
        )
        assert state == "dead_letter"
        assert repository.counts() == {"dead_letter": 1}
        assert repository.replay_dead_letter(record_id) is True
        assert repository.counts() == {"queued": 1}


def test_worker_claims_and_completes_event(monkeypatch, organization_id):
    event_id = f"worker-{uuid4().hex}"
    with SessionLocal() as db:
        set_tenant_context(db, organization_id)
        EventQueueRepository(db, organization_id).enqueue(build_event(event_id))

    processed: list[str] = []

    def process(_db, record):
        processed.append(record.event_id)

    monkeypatch.setattr(settings, "EVENT_QUEUE_BATCH_SIZE", 100)
    totals = EventIngestionWorker(
        worker_id="unit-test-worker",
        processor=process,
        archiver=StubArchive(),
    ).run_once()

    assert event_id in processed
    assert totals["completed"] >= 1
    assert totals["archived"] >= 1
    with SessionLocal() as db:
        set_tenant_context(db, organization_id)
        assert EventQueueRepository(db, organization_id).counts() == {"completed": 1}


def test_retention_removes_only_archived_completed_events(organization_id):
    old = datetime.now(timezone.utc) - timedelta(days=60)
    with SessionLocal() as db:
        set_tenant_context(db, organization_id)
        db.add_all(
            [
                SecurityEventRecord(
                    organization_id=organization_id,
                    event_id=f"archived-{uuid4().hex}",
                    source="cloudtrail",
                    raw_event={},
                    normalized_event={},
                    status="completed",
                    attempts=1,
                    max_attempts=5,
                    available_at=old,
                    received_at=old,
                    processed_at=old,
                    archived_at=old,
                    archive_uri="memory://archived",
                    archive_sha256="b" * 64,
                ),
                SecurityEventRecord(
                    organization_id=organization_id,
                    event_id=f"unarchived-{uuid4().hex}",
                    source="cloudtrail",
                    raw_event={},
                    normalized_event={},
                    status="completed",
                    attempts=1,
                    max_attempts=5,
                    available_at=old,
                    received_at=old,
                    processed_at=old,
                ),
            ]
        )
        db.commit()
        repository = EventQueueRepository(db, organization_id)
        assert repository.purge_archived_completed(
            retention_days=30,
            batch_size=100,
        ) == 1
        assert repository.counts() == {"completed": 1}
