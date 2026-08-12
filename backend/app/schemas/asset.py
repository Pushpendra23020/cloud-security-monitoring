from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    cloud_account_id: int

    asset_type: str = Field(
        min_length=2,
        max_length=50,
        examples=["ec2_instance"],
    )

    asset_id: str = Field(
        min_length=1,
        max_length=255,
        examples=["i-0123456789abcdef0"],
    )

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    region: str | None = Field(
        default=None,
        max_length=50,
        examples=["ap-south-1"],
    )


class AssetResponse(BaseModel):
    id: int
    cloud_account_id: int
    asset_type: str
    asset_id: str
    name: str | None
    region: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
