from app.rules.rule import RuleCondition
from app.rules.threshold import ThresholdRule


AWS_CORRELATION_RULES = [
    ThresholdRule(
        rule_id="AWS-CORR-001",
        name="Possible AWS Console Brute Force",
        description=(
            "Detects multiple failed AWS console "
            "login attempts from the same source IP."
        ),
        severity="high",
        cloud_provider="aws",
        service="signin",
        event_name="ConsoleLogin",
        conditions=[
            RuleCondition(
                field=(
                    "raw_event."
                    "responseElements."
                    "ConsoleLogin"
                ),
                operator="equals",
                value="Failure",
            )
        ],
        threshold=5,
        window_minutes=10,
        group_by="source_ip",
        mitre_tactic="Credential Access",
        mitre_technique="Brute Force",
        mitre_technique_id="T1110",
    ),
]

