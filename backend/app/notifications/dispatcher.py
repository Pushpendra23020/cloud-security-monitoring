from datetime import datetime, timezone
from typing import Iterable

from app.models.alert import Alert
from app.notifications.base import (
    AlertNotifier,
)
from app.services.alert_notification_policy import (
    AlertNotificationPolicy,
)


class NotificationDispatcher:

    def __init__(
        self,
        notifiers: Iterable[
            AlertNotifier
        ] | None = None,
    ):
        self.notifiers = list(
            notifiers or []
        )

    def dispatch(
        self,
        alert: Alert,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = (
            now
            or datetime.now(timezone.utc)
        )

        allowed = (
            AlertNotificationPolicy.apply_policy(
                alert,
                now=current_time,
            )
        )

        if not allowed:
            return False

        if not self.notifiers:
            AlertNotificationPolicy.mark_failed(
                alert,
                now=current_time,
            )

            return False

        success = False

        for notifier in self.notifiers:
            try:
                result = notifier.send(
                    alert
                )

                if result:
                    success = True

            except Exception:
                continue

        if success:
            AlertNotificationPolicy.mark_sent(
                alert,
                now=current_time,
            )

            return True

        AlertNotificationPolicy.mark_failed(
            alert,
            now=current_time,
        )

        return False
