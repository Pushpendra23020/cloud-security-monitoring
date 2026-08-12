from typing import List, Optional

from pydantic import BaseModel, Field

from app.rules.rule import RuleCondition


class ThresholdRule(BaseModel):
    rule_id: str
    name: str
    description: Optional[str] = None

    severity: str

    cloud_provider: str = "aws"
    service: Optional[str] = None
    event_name: Optional[str] = None

    conditions: List[RuleCondition] = Field(
        default_factory=list
    )

    threshold: int
    window_minutes: int

    group_by: str

    enabled: bool = True

    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_technique_id: Optional[str] = None
