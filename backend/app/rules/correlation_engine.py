import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.rules.evaluator import ConditionEvaluator
from app.rules.history import EventHistoryBuffer
from app.rules.threshold import ThresholdRule


class CorrelationEngine:
    def __init__(
        self,
        rules: List[ThresholdRule],
        history: EventHistoryBuffer | None = None,
        cooldown_minutes: int = 10,
    ):
        self.rules = rules

        self.history = (
            history
            or EventHistoryBuffer()
        )

        self.cooldown = timedelta(
            minutes=cooldown_minutes
        )

        self._last_alert_times: Dict[
            Tuple[str, str],
            datetime,
        ] = {}

    def process(
        self,
        event: SecurityEvent,
    ) -> List[Alert]:
        self.history.add(event)

        alerts: List[Alert] = []

        for rule in self.rules:
            alert = self.evaluate_rule(
                event,
                rule,
            )

            if alert is not None:
                alerts.append(alert)

        return alerts

    def _is_suppressed(
        self,
        rule_id: str,
        group_value: str,
        current_time: datetime,
    ) -> bool:
        key = (
            rule_id,
            str(group_value),
        )

        last_alert_time = (
            self._last_alert_times.get(key)
        )

        if last_alert_time is None:
            return False

        return (
            current_time - last_alert_time
            < self.cooldown
        )

    def _record_alert(
        self,
        rule_id: str,
        group_value: str,
        alert_time: datetime,
    ) -> None:
        key = (
            rule_id,
            str(group_value),
        )

        self._last_alert_times[key] = (
            alert_time
        )

    def evaluate_rule(
        self,
        event: SecurityEvent,
        rule: ThresholdRule,
    ) -> Alert | None:
        if not rule.enabled:
            return None

        if (
            rule.cloud_provider
            and event.cloud_provider
            != rule.cloud_provider
        ):
            return None

        if (
            rule.service
            and event.service
            != rule.service
        ):
            return None

        if (
            rule.event_name
            and event.event_name
            != rule.event_name
        ):
            return None

        for condition in rule.conditions:
            if not ConditionEvaluator.evaluate(
                event,
                condition,
            ):
                return None

        group_value = (
            ConditionEvaluator.get_field_value(
                event,
                rule.group_by,
            )
        )

        if group_value is None:
            return None

        since = (
            event.timestamp
            - timedelta(
                minutes=rule.window_minutes
            )
        )

        matching_events = []

        for historical_event in (
            self.history.get_events()
        ):
            if (
                historical_event.timestamp
                < since
            ):
                continue

            if (
                rule.service
                and historical_event.service
                != rule.service
            ):
                continue

            if (
                rule.event_name
                and historical_event.event_name
                != rule.event_name
            ):
                continue

            historical_group = (
                ConditionEvaluator.get_field_value(
                    historical_event,
                    rule.group_by,
                )
            )

            if (
                historical_group
                != group_value
            ):
                continue

            if not all(
                ConditionEvaluator.evaluate(
                    historical_event,
                    condition,
                )
                for condition
                in rule.conditions
            ):
                continue

            matching_events.append(
                historical_event
            )

        if (
            len(matching_events)
            < rule.threshold
        ):
            return None

        if self._is_suppressed(
            rule.rule_id,
            str(group_value),
            event.timestamp,
        ):
            return None

        detection_key = hashlib.sha256(
            (
                f"{rule.rule_id}:"
                f"{group_value}:"
                f"{matching_events[0].event_id}:"
                f"{matching_events[-1].event_id}"
            ).encode("utf-8")
        ).hexdigest()

        alert = Alert(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            description=rule.description,
            severity=rule.severity,

            event_id=event.event_id,
            event_name=event.event_name,

            detection_key=detection_key,

            cloud_provider=(
                event.cloud_provider
            ),
            account_id=event.account_id,
            region=event.region,
            service=event.service,
            source_ip=event.source_ip,
            user_identity=(
                event.user_identity
            ),

            mitre_tactic=(
                rule.mitre_tactic
            ),
            mitre_technique=(
                rule.mitre_technique
            ),
            mitre_technique_id=(
                rule.mitre_technique_id
            ),

            metadata={
                "threshold": (
                    rule.threshold
                ),
                "window_minutes": (
                    rule.window_minutes
                ),
                "cooldown_minutes": (
                    int(
                        self.cooldown.total_seconds()
                        / 60
                    )
                ),
                "group_by": (
                    rule.group_by
                ),
                "group_value": (
                    group_value
                ),
                "matched_event_ids": [
                    item.event_id
                    for item
                    in matching_events
                ],
                "matched_event_count": (
                    len(
                        matching_events
                    )
                ),
            },
        )

        self._record_alert(
            rule.rule_id,
            str(group_value),
            event.timestamp,
        )

        return alert
