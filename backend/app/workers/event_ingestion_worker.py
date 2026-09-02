import logging
import os
import socket
import time
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.runtime_security import validate_worker_runtime_security
from app.database.models.organization import Organization
from app.database.models.security_event import SecurityEventRecord
from app.database.session import SessionLocal, set_tenant_context, validate_rls_enforcement
from app.repositories.event_queue_repository import EventQueueRepository
from app.services.durable_event_processing_service import DurableEventProcessingService
from app.services.event_archive_service import EventArchive, build_event_archive
from app.utils.metrics import (
    EVENT_QUEUE_PROCESSING_SECONDS,
    EVENT_QUEUE_TRANSITIONS_TOTAL,
)


logger = logging.getLogger(__name__)


class EventIngestionWorker:
    def __init__(
        self,
        *,
        worker_id: str | None = None,
        processor: Callable[[Session, SecurityEventRecord], None] | None = None,
        archiver: EventArchive | None = None,
    ):
        self.worker_id = worker_id or (
            f"{socket.gethostname()}-{os.getpid()}"
        )
        self.processor = processor or DurableEventProcessingService.process
        self.archiver = archiver or build_event_archive()
        self.last_cleanup_at = 0.0

    def run_once(self) -> dict[str, int]:
        totals = {
            "claimed": 0,
            "archived": 0,
            "completed": 0,
            "retried": 0,
            "dead_letter": 0,
            "purged": 0,
        }
        cleanup_due = (
            time.monotonic() - self.last_cleanup_at
            >= settings.EVENT_RETENTION_CLEANUP_INTERVAL_SECONDS
        )
        with SessionLocal() as discovery_db:
            organization_ids = list(
                discovery_db.scalars(
                    select(Organization.id).where(Organization.is_active.is_(True))
                )
            )

        for organization_id in organization_ids:
            with SessionLocal() as claim_db:
                set_tenant_context(claim_db, organization_id)
                records = EventQueueRepository(
                    claim_db,
                    organization_id,
                ).claim_batch(
                    worker_id=self.worker_id,
                    batch_size=settings.EVENT_QUEUE_BATCH_SIZE,
                    lock_timeout_seconds=settings.EVENT_QUEUE_LOCK_TIMEOUT_SECONDS,
                )
            totals["claimed"] += len(records)

            for record in records:
                started = time.monotonic()
                try:
                    if record.archive_uri is None:
                        archive = self.archiver.archive(record)
                        with SessionLocal() as archive_db:
                            set_tenant_context(archive_db, organization_id)
                            EventQueueRepository(
                                archive_db,
                                organization_id,
                            ).mark_archived(
                                record.id,
                                uri=archive.uri,
                                sha256=archive.sha256,
                                archived_at=archive.archived_at,
                                retention_until=archive.retention_until,
                            )
                        totals["archived"] += 1
                    with SessionLocal() as processing_db:
                        set_tenant_context(processing_db, organization_id)
                        self.processor(processing_db, record)
                    with SessionLocal() as status_db:
                        set_tenant_context(status_db, organization_id)
                        EventQueueRepository(
                            status_db,
                            organization_id,
                        ).mark_completed(record.id)
                    result = "completed"
                    totals["completed"] += 1
                except Exception as exc:
                    logger.exception(
                        "durable_event_processing_failed",
                        extra={
                            "organization_id": organization_id,
                            "event_id": record.event_id,
                            "worker_id": self.worker_id,
                        },
                    )
                    with SessionLocal() as status_db:
                        set_tenant_context(status_db, organization_id)
                        result = EventQueueRepository(
                            status_db,
                            organization_id,
                        ).mark_failed(
                            record.id,
                            exc,
                            base_delay=settings.EVENT_QUEUE_RETRY_BASE_SECONDS,
                        )
                    if result == "dead_letter":
                        totals["dead_letter"] += 1
                    else:
                        totals["retried"] += 1

                EVENT_QUEUE_TRANSITIONS_TOTAL.labels(
                    source=record.source,
                    result=result,
                ).inc()
                EVENT_QUEUE_PROCESSING_SECONDS.labels(
                    source=record.source,
                    result=result,
                ).observe(time.monotonic() - started)

            if cleanup_due:
                with SessionLocal() as cleanup_db:
                    set_tenant_context(cleanup_db, organization_id)
                    totals["purged"] += EventQueueRepository(
                        cleanup_db,
                        organization_id,
                    ).purge_archived_completed(
                        retention_days=settings.EVENT_DATABASE_RETENTION_DAYS,
                        batch_size=settings.EVENT_RETENTION_CLEANUP_BATCH_SIZE,
                    )

        if cleanup_due:
            self.last_cleanup_at = time.monotonic()

        return totals


def main() -> None:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    validate_worker_runtime_security()
    validate_rls_enforcement()
    worker = EventIngestionWorker()
    logger.info("durable_event_worker_started", extra={"worker_id": worker.worker_id})
    while True:
        try:
            totals = worker.run_once()
            if totals["claimed"]:
                logger.info("durable_event_worker_batch", extra=totals)
        except Exception:
            logger.exception("durable_event_worker_iteration_failed")
        time.sleep(settings.EVENT_QUEUE_POLL_SECONDS)


if __name__ == "__main__":
    main()
