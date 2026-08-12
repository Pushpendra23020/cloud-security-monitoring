from typing import List

from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.rules.aws_correlation_rules import (
    AWS_CORRELATION_RULES,
)
from app.rules.aws_rules import AWS_RULES
from app.rules.correlation_engine import (
    CorrelationEngine,
)
from app.rules.engine import DetectionEngine
from app.services.alert_service import AlertService
from app.services.incident_factory import (
    IncidentFactory,
)
from app.services.incident_service import (
    IncidentService,
)


class DetectionPipeline:
    def __init__(
        self,
        engine: DetectionEngine | None = None,
        correlation_engine: CorrelationEngine | None = None,
        alert_service: AlertService | None = None,
        incident_service: IncidentService | None = None,
    ):
        self.engine = (
            engine
            or DetectionEngine(
                AWS_RULES
            )
        )

        self.correlation_engine = (
            correlation_engine
            or CorrelationEngine(
                AWS_CORRELATION_RULES
            )
        )

        self.alert_service = (
            alert_service
            or AlertService()
        )

        self.incident_service = (
            incident_service
        )

    def process(
        self,
        event: SecurityEvent,
    ) -> List[Alert]:
        alerts: List[Alert] = []

        # Single-event detections
        alerts.extend(
            self.engine.evaluate(
                event
            )
        )

        # Correlation / threshold detections
        correlation_alerts = (
            self.correlation_engine.process(
                event
            )
        )

        alerts.extend(
            correlation_alerts
        )

        # Persist alerts individually so we know
        # which alerts were newly stored.
        for alert in alerts:
            saved = (
                self.alert_service.save_alert(
                    alert
                )
            )

            if not saved:
                continue

            # Only correlation alerts create incidents.
            if (
                alert
                not in correlation_alerts
            ):
                continue

            if self.incident_service is None:
                continue

            incident = (
                IncidentFactory
                .from_correlation_alert(
                    alert
                )
            )

            incident_saved = (
                self.incident_service
                .save_incident(
                    incident
                )
            )

            if not incident_saved:
                continue

            # Link the correlation alert
            # back to the incident.
            alert.incident_id = (
                incident.incident_id
            )

            self.alert_service.update_alert(
                alert
            )

        return alerts
