from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    cloud_account_id: int

    asset_type: str = Field(
        min_length=2,
        max_length=50,
    )

    asset_id: str = Field(
        min_length=1,
        max_length=255,
    )

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    region: str | None = Field(
        default=None,
        max_length=50,
    )

    risk_score: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    risk_level: str = Field(
        default="low",
        max_length=20,
    )

    findings_count: int = Field(
        default=0,
        ge=0,
    )

    alerts_count: int = Field(
        default=0,
        ge=0,
    )

    public_exposure: bool = False

    resource_state: str = Field(
        default="unknown",
        max_length=50,
    )

    tags: dict[str, Any] = Field(
        default_factory=dict,
    )

    last_seen: datetime | None = None


class AssetResponse(BaseModel):
    id: int
    cloud_account_id: int

    asset_type: str
    asset_id: str

    name: str | None
    region: str | None

    risk_score: int
    risk_level: str

    findings_count: int
    alerts_count: int

    public_exposure: bool
    resource_state: str

    tags: dict[str, Any]

    last_seen: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

    risk_updated_at: datetime | None
