from datetime import datetime, timedelta, timezone

from app.models.alert import (
    Alert,
    AlertSeverity,
    NotificationStatus,
)


class AlertNotificationPolicy:
    THROTTLE_WINDOWS = {
        AlertSeverity.CRITICAL: timedelta(
            minutes=1
        ),
        AlertSeverity.HIGH: timedelta(
            minutes=5
        ),
        AlertSeverity.MEDIUM: timedelta(
            minutes=15
        ),
        AlertSeverity.LOW: timedelta(
            minutes=30
        ),
        AlertSeverity.INFO: timedelta(
            minutes=60
        ),
    }

    @classmethod
    def should_notify(
        cls,
        alert: Alert,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        if current_time.tzinfo is None:
            current_time = (
                current_time.replace(
                    tzinfo=timezone.utc
                )
            )

        if alert.suppressed_until is not None:
            suppressed_until = (
                alert.suppressed_until
            )

            if suppressed_until.tzinfo is None:
                suppressed_until = (
                    suppressed_until.replace(
                        tzinfo=timezone.utc
                    )
                )

            if suppressed_until > current_time:
                return False

        if alert.last_notified_at is None:
            return True

        last_notified_at = (
            alert.last_notified_at
        )

        if last_notified_at.tzinfo is None:
            last_notified_at = (
                last_notified_at.replace(
                    tzinfo=timezone.utc
                )
            )

        throttle_window = (
            cls.THROTTLE_WINDOWS[
                alert.severity
            ]
        )

        next_allowed_at = (
            last_notified_at
            + throttle_window
        )

        return (
            current_time
            >= next_allowed_at
        )

    @classmethod
    def apply_policy(
        cls,
        alert: Alert,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        allowed = cls.should_notify(
            alert,
            now=current_time,
        )

        if allowed:
            alert.notification_status = (
                NotificationStatus.PENDING
            )

            if (
                alert.suppressed_until
                is not None
                and alert.suppressed_until
                <= current_time
            ):
                alert.suppressed_until = None

            return True

        alert.notification_status = (
            NotificationStatus.SUPPRESSED
        )

        return False

    @staticmethod
    def mark_sent(
        alert: Alert,
        *,
        now: datetime | None = None,
    ) -> None:
        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        alert.notification_status = (
            NotificationStatus.SENT
        )
        alert.last_notified_at = (
            current_time
        )
        alert.updated_at = current_time

    @staticmethod
    def mark_failed(
        alert: Alert,
        *,
        now: datetime | None = None,
    ) -> None:
        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        alert.notification_status = (
            NotificationStatus.FAILED
        )
        alert.updated_at = current_time

    @staticmethod
    def suppress_until(
        alert: Alert,
        until: datetime,
        *,
        now: datetime | None = None,
    ) -> None:
        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        alert.suppressed_until = until
        alert.notification_status = (
            NotificationStatus.SUPPRESSED
        )
        alert.updated_at = current_time
