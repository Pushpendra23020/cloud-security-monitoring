from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    field: str
    operator: str = "equals"
    value: Any


class DetectionRule(BaseModel):
    rule_id: str
    name: str
    description: Optional[str] = None

    cloud_provider: str = "aws"
    event_name: Optional[str] = None
    service: Optional[str] = None

    severity: str

    enabled: bool = True

    conditions: List[RuleCondition] = Field(default_factory=list)

    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_technique_id: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
