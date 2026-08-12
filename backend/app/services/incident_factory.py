from app.models.alert import Alert
from app.models.incident import Incident


class IncidentFactory:
    @staticmethod
    def from_correlation_alert(
        alert: Alert,
    ) -> Incident:
        event_ids = list(
            alert.metadata.get(
                "matched_event_ids",
                [],
            )
        )

        if (
            alert.event_id
            and alert.event_id not in event_ids
        ):
            event_ids.append(
                alert.event_id
            )

        return Incident(
            title=alert.rule_name,
            description=alert.description,
            severity=alert.severity,
            cloud_provider=alert.cloud_provider,
            account_id=alert.account_id,
            region=alert.region,
            source_ip=alert.source_ip,
            user_identity=alert.user_identity,
            correlation_rule_id=alert.rule_id,
            alert_ids=[
                alert.alert_id
            ],
            event_ids=event_ids,
            mitre_tactic=alert.mitre_tactic,
            mitre_technique=(
                alert.mitre_technique
            ),
            mitre_technique_id=(
                alert.mitre_technique_id
            ),
            metadata={
                **alert.metadata,
                "source_alert_id": (
                    alert.alert_id
                ),
            },
        )
