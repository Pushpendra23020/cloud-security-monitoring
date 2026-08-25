from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CloudAccountCreate(BaseModel):
    name: str = Field(default="AWS Account", min_length=2, max_length=120)
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
    auth_method: str = Field(default="assume_role", pattern="^assume_role$")
    role_arn: str | None = Field(default=None, min_length=20, max_length=2048)
    external_id: str | None = Field(default=None, min_length=8, max_length=255)
    monitoring_enabled: bool = True
    services: list[str] = Field(default_factory=lambda: ["cloudtrail", "guardduty", "config", "iam", "ec2", "s3"])
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("provider")
    @classmethod
    def aws_only(cls, value: str) -> str:
        if value.lower() != "aws":
            raise ValueError("AWS is the only supported provider for onboarding.")
        return "aws"


class CloudAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    region: str | None = Field(default=None, max_length=50)
    role_arn: str | None = Field(default=None, min_length=20, max_length=2048)
    external_id: str | None = Field(default=None, min_length=8, max_length=255)
    monitoring_enabled: bool | None = None
    services: list[str] | None = None
    description: str | None = Field(default=None, max_length=2000)


class CloudAccountResponse(BaseModel):
    id: int
    provider: str
    name: str
    account_id: str
    region: str | None
    auth_method: str
    role_arn: str | None
    monitoring_enabled: bool
    services: list[str]
    description: str | None
    health_status: str
    last_sync: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CloudAccountConnectionResponse(BaseModel):
    success: bool
    account_id: str | None = None
    region: str
    role_arn: str
    permissions: dict[str, bool]
    message: str
