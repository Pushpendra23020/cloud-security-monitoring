from uuid import uuid4

from sqlalchemy import delete

from app.database.models.alert import Alert as AlertDB
from app.database.session import SessionLocal
from app.models.alert import Alert
from app.repositories.postgres_alert_repository import (
    PostgresAlertRepository,
)


def build_alert(
    alert_id: str | None = None,
    detection_key: str | None = None,
) -> Alert:
    unique = str(uuid4())

    return Alert(
        alert_id=alert_id or f"alert-{unique}",
        rule_id="AWS-TEST-001",
        rule_name="PostgreSQL Repository Test",
        description=(
            "Test alert for PostgreSQL persistence."
        ),
        severity="high",
        event_id=f"event-{unique}",
        event_name="ConsoleLogin",
        detection_key=(
            detection_key
            or f"detection-{unique}"
        ),
        cloud_provider="aws",
        account_id="123456789012",
        region="us-east-1",
        service="signin",
        source_ip="192.0.2.10",
        user_identity="test-user",
        metadata={
            "test": True,
            "source": "pytest",
        },
    )


def cleanup_alert(
    alert_id: str,
) -> None:
    with SessionLocal() as session:
        session.execute(
            delete(AlertDB).where(
                AlertDB.alert_id == alert_id
            )
        )

        session.commit()


def test_postgres_repository_save_and_get():
    alert = build_alert()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresAlertRepository(
                    session
                )
            )

            assert repository.save(
                alert
            ) is True

            stored = repository.get(
                alert.alert_id
            )

            assert stored is not None
            assert (
                stored.alert_id
                == alert.alert_id
            )
            assert stored.rule_id == alert.rule_id
            assert stored.severity == "high"
            assert stored.status == "open"

            assert (
                stored.cloud_provider
                == "aws"
            )

            assert stored.metadata == {
                "test": True,
                "source": "pytest",
            }

    finally:
        cleanup_alert(alert.alert_id)


def test_postgres_repository_update():
    alert = build_alert()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresAlertRepository(
                    session
                )
            )

            assert repository.save(
                alert
            ) is True

            stored = repository.get(
                alert.alert_id
            )

            assert stored is not None

            stored.description = (
                "Updated PostgreSQL alert"
            )

            stored.status = "investigating"

            assert repository.update(
                stored
            ) is True

            updated = repository.get(
                alert.alert_id
            )

            assert updated is not None

            assert (
                updated.description
                == "Updated PostgreSQL alert"
            )

            assert (
                updated.status
                == "investigating"
            )

    finally:
        cleanup_alert(alert.alert_id)


def test_postgres_repository_duplicate_alert_id():
    alert = build_alert()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresAlertRepository(
                    session
                )
            )

            assert repository.save(
                alert
            ) is True

            duplicate = alert.model_copy(
                deep=True
            )

            assert repository.save(
                duplicate
            ) is False

    finally:
        cleanup_alert(alert.alert_id)


def test_postgres_repository_duplicate_detection():
    detection_key = (
        f"detection-{uuid4()}"
    )

    first = build_alert(
        detection_key=detection_key
    )

    second = build_alert(
        detection_key=detection_key
    )

    try:
        with SessionLocal() as session:
            repository = (
                PostgresAlertRepository(
                    session
                )
            )

            assert repository.save(
                first
            ) is True

            assert repository.save(
                second
            ) is False

    finally:
        cleanup_alert(first.alert_id)
        cleanup_alert(second.alert_id)


def test_postgres_repository_load_all():
    first = build_alert()
    second = build_alert()

    try:
        with SessionLocal() as session:
            repository = (
                PostgresAlertRepository(
                    session
                )
            )

            assert repository.save(
                first
            ) is True

            assert repository.save(
                second
            ) is True

            alerts = repository.load_all()

            ids = {
                alert.alert_id
                for alert in alerts
            }

            assert first.alert_id in ids
            assert second.alert_id in ids

    finally:
        cleanup_alert(first.alert_id)
        cleanup_alert(second.alert_id)
