from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

UserRole = Literal["admin", "analyst", "viewer"]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=12, max_length=1024)
    role: UserRole = "analyst"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    mfa_enabled: bool
    oidc_linked: bool


class UserStatusUpdate(BaseModel):
    is_active: bool


class OidcIdentityUpdate(BaseModel):
    issuer: str = Field(min_length=8, max_length=500, pattern=r"^https://")
    subject: str = Field(min_length=1, max_length=255)


class OidcIdentityResponse(BaseModel):
    user_id: int
    issuer: str
    subject: str


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    user: str
    method: str | None
    path: str | None
    status_code: int | None
    client_ip: str | None
    created_at: datetime
