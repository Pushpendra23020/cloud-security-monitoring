import base64
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.database.models.security_event import SecurityEventRecord


@dataclass(frozen=True)
class ArchiveResult:
    uri: str
    sha256: str
    archived_at: datetime
    retention_until: datetime | None


class EventArchive(Protocol):
    def archive(self, record: SecurityEventRecord) -> ArchiveResult: ...


def canonical_event_payload(record: SecurityEventRecord) -> bytes:
    envelope = {
        "event_id": record.event_id,
        "organization_id": record.organization_id,
        "received_at": record.received_at.isoformat(),
        "source": record.source,
        "raw_event": record.raw_event,
        "normalized_event": record.normalized_event,
    }
    return json.dumps(
        envelope,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


class FilesystemEventArchive:
    def __init__(self, base_path: str, retention_days: int):
        self.base_path = Path(base_path)
        self.retention_days = retention_days

    def archive(self, record: SecurityEventRecord) -> ArchiveResult:
        payload = canonical_event_payload(record)
        digest = hashlib.sha256(payload).hexdigest()
        received_at = record.received_at.astimezone(timezone.utc)
        path = (
            self.base_path
            / f"organization-{record.organization_id}"
            / received_at.strftime("%Y")
            / received_at.strftime("%m")
            / received_at.strftime("%d")
            / f"{digest}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as archive_file:
                archive_file.write(payload)
            os.chmod(path, 0o440)
        except FileExistsError:
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError("Existing event archive failed integrity verification.")

        archived_at = datetime.now(timezone.utc)
        retention_until = archived_at + timedelta(days=self.retention_days)
        return ArchiveResult(
            uri=path.resolve().as_uri(),
            sha256=digest,
            archived_at=archived_at,
            retention_until=retention_until,
        )


class S3EventArchive:
    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        retention_days: int,
        kms_key_id: str | None = None,
        client=None,
    ):
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.retention_days = retention_days
        self.kms_key_id = kms_key_id
        self.client = client or boto3.client("s3", region_name=settings.AWS_REGION)

    def archive(self, record: SecurityEventRecord) -> ArchiveResult:
        payload = canonical_event_payload(record)
        digest = hashlib.sha256(payload).hexdigest()
        checksum = base64.b64encode(hashlib.sha256(payload).digest()).decode("ascii")
        received_at = record.received_at.astimezone(timezone.utc)
        key = "/".join(
            part
            for part in (
                self.prefix,
                f"organization-{record.organization_id}",
                received_at.strftime("%Y/%m/%d"),
                f"{digest}.json",
            )
            if part
        )
        archived_at = datetime.now(timezone.utc)
        retention_until = archived_at + timedelta(days=self.retention_days)
        request = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": payload,
            "ContentType": "application/json",
            "ChecksumSHA256": checksum,
            "IfNoneMatch": "*",
            "Metadata": {"sha256": digest},
            "ObjectLockMode": "COMPLIANCE",
            "ObjectLockRetainUntilDate": retention_until,
        }
        if self.kms_key_id:
            request.update(
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self.kms_key_id,
            )
        else:
            request["ServerSideEncryption"] = "AES256"

        try:
            self.client.put_object(**request)
        except ClientError as exc:
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code not in {409, 412}:
                raise
            existing = self.client.head_object(Bucket=self.bucket, Key=key)
            if existing.get("Metadata", {}).get("sha256") != digest:
                raise RuntimeError("Existing S3 archive failed integrity verification.") from exc

        return ArchiveResult(
            uri=f"s3://{self.bucket}/{key}",
            sha256=digest,
            archived_at=archived_at,
            retention_until=retention_until,
        )


def build_event_archive() -> EventArchive:
    provider = settings.EVENT_ARCHIVE_PROVIDER.strip().lower()
    if provider == "filesystem":
        return FilesystemEventArchive(
            settings.EVENT_ARCHIVE_PATH,
            settings.EVENT_ARCHIVE_RETENTION_DAYS,
        )
    if provider == "s3":
        if not settings.EVENT_ARCHIVE_S3_BUCKET:
            raise RuntimeError(
                "EVENT_ARCHIVE_S3_BUCKET is required for the S3 archive provider."
            )
        return S3EventArchive(
            bucket=settings.EVENT_ARCHIVE_S3_BUCKET,
            prefix=settings.EVENT_ARCHIVE_S3_PREFIX,
            retention_days=settings.EVENT_ARCHIVE_RETENTION_DAYS,
            kms_key_id=settings.EVENT_ARCHIVE_S3_KMS_KEY_ID,
        )
    raise RuntimeError(f"Unsupported EVENT_ARCHIVE_PROVIDER: {provider}")
