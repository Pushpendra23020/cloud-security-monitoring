from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CloudAccountCreate(BaseModel):
    provider: str = Field(
        min_length=2,
        max_length=20,
        examples=["aws"],
    )
    account_id: str = Field(
        min_length=3,
        max_length=100,
        examples=["123456789012"],
    )
    region: str | None = Field(
        default=None,
        max_length=50,
        examples=["ap-south-1"],
    )


class CloudAccountResponse(BaseModel):
    id: int
    provider: str
    account_id: str
    region: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
