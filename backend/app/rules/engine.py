import hashlib
from typing import Iterable, List

from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.rules.evaluator import ConditionEvaluator
from app.rules.rule import DetectionRule


class DetectionEngine:
    def __init__(
        self,
        rules: Iterable[DetectionRule] | None = None,
    ):
        self.rules = list(rules or [])

    def add_rule(
        self,
        rule: DetectionRule,
    ) -> None:
        self.rules.append(rule)

    def rule_matches(
        self,
        event: SecurityEvent,
        rule: DetectionRule,
    ) -> bool:
        if not rule.enabled:
            return False

        if (
            rule.cloud_provider
            and event.cloud_provider != rule.cloud_provider
        ):
            return False

        if (
            rule.event_name
            and event.event_name != rule.event_name
        ):
            return False

        if (
            rule.service
            and event.service != rule.service
        ):
            return False

        for condition in rule.conditions:
            if not ConditionEvaluator.evaluate(
                event,
                condition,
            ):
                return False

        return True

    def create_alert(
        self,
        event: SecurityEvent,
        rule: DetectionRule,
    ) -> Alert:
        detection_key = hashlib.sha256(
            f"{rule.rule_id}:{event.event_id}".encode(
                "utf-8"
            )
        ).hexdigest()

        return Alert(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            description=rule.description,
            severity=rule.severity,

            event_id=event.event_id,
            event_name=event.event_name,
            detection_key=detection_key,

            cloud_provider=event.cloud_provider,
            account_id=event.account_id,
            region=event.region,
            service=event.service,
            source_ip=event.source_ip,
            user_identity=event.user_identity,
            
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            
            mitre_tactic=rule.mitre_tactic,
            mitre_technique=rule.mitre_technique,
            mitre_technique_id=rule.mitre_technique_id,
            
            metadata={
                "rule_metadata": rule.metadata,
},
        )
    def evaluate(
        self,
        event: SecurityEvent,
    ) -> List[Alert]:
        alerts: List[Alert] = []

        for rule in self.rules:
            if self.rule_matches(
                event,
                rule,
            ):
                alerts.append(
                    self.create_alert(
                        event,
                        rule,
                    )
                )

        return alerts
