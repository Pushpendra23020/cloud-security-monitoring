from typing import List

from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.rules.aws_correlation_rules import AWS_CORRELATION_RULES
from app.rules.aws_rules import AWS_RULES
from app.rules.correlation_engine import CorrelationEngine
from app.rules.engine import DetectionEngine
from app.services.alert_service import AlertService


class DetectionPipeline:
    def __init__(
        self,
        engine: DetectionEngine | None = None,
        correlation_engine: CorrelationEngine | None = None,
        alert_service: AlertService | None = None,
    ):
        self.engine = (
            engine
            or DetectionEngine(AWS_RULES)
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

    def process(
        self,
        event: SecurityEvent,
    ) -> List[Alert]:
        alerts: List[Alert] = []

        # Single-event detections
        alerts.extend(
            self.engine.evaluate(event)
        )

        # Correlation / threshold detections
        alerts.extend(
            self.correlation_engine.process(
                event
            )
        )

        # Persist all detections
        self.alert_service.save_alerts(
            alerts
        )

        return alerts
