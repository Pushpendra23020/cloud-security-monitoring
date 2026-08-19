from app.models.alert import Alert
from app.notifications.base import (
    AlertNotifier,
)


class ConsoleNotifier(AlertNotifier):

    def send(
        self,
        alert: Alert,
    ) -> bool:
        try:
            print(
                "[SECURITY ALERT] "
                f"{alert.severity.value.upper()} | "
                f"{alert.rule_name} | "
                f"alert_id={alert.alert_id} | "
                f"resource={alert.resource_id or 'unknown'} | "
                f"occurrences={alert.occurrence_count}"
            )

            return True

        except Exception:
            return False
