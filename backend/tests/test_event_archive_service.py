import hashlib
from datetime import datetime, timezone

import pytest

from app.database.models.security_event import SecurityEventRecord
from app.services.event_archive_service import (
    FilesystemEventArchive,
    S3EventArchive,
    canonical_event_payload,
)


def build_record() -> SecurityEventRecord:
    return SecurityEventRecord(
        id=1,
        organization_id=7,
        event_id="archive-event-1",
        source="cloudtrail",
        raw_event={"eventID": "archive-event-1", "answer": 42},
        normalized_event={
            "event_id": "archive-event-1",
            "timestamp": "2026-08-27T00:00:00Z",
            "cloud_provider": "aws",
            "event_name": "DescribeInstances",
        },
        status="processing",
        attempts=1,
        max_attempts=5,
        available_at=datetime.now(timezone.utc),
        received_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
    )


def test_filesystem_archive_is_content_addressed_and_idempotent(tmp_path):
    record = build_record()
    archive = FilesystemEventArchive(str(tmp_path), retention_days=365)

    first = archive.archive(record)
    second = archive.archive(record)

    assert first.uri == second.uri
    assert first.sha256 == hashlib.sha256(canonical_event_payload(record)).hexdigest()
    assert first.retention_until > first.archived_at
    archive_path = next(tmp_path.rglob("*.json"))
    assert archive_path.read_bytes() == canonical_event_payload(record)
    assert archive_path.stat().st_mode & 0o777 == 0o440


def test_filesystem_archive_rejects_integrity_mismatch(tmp_path):
    record = build_record()
    archive = FilesystemEventArchive(str(tmp_path), retention_days=365)
    archive.archive(record)
    archive_path = next(tmp_path.rglob("*.json"))
    archive_path.chmod(0o640)
    archive_path.write_text("tampered", encoding="utf-8")

    with pytest.raises(RuntimeError, match="integrity"):
        archive.archive(record)


def test_s3_archive_requests_compliance_retention_and_encryption():
    class FakeS3Client:
        request = None

        def put_object(self, **kwargs):
            self.request = kwargs

    client = FakeS3Client()
    result = S3EventArchive(
        bucket="security-archive",
        prefix="events",
        retention_days=365,
        kms_key_id="kms-key-id",
        client=client,
    ).archive(build_record())

    assert result.uri.startswith("s3://security-archive/events/organization-7/")
    assert client.request["IfNoneMatch"] == "*"
    assert client.request["ObjectLockMode"] == "COMPLIANCE"
    assert client.request["ServerSideEncryption"] == "aws:kms"
    assert client.request["SSEKMSKeyId"] == "kms-key-id"
    assert client.request["Metadata"]["sha256"] == result.sha256
