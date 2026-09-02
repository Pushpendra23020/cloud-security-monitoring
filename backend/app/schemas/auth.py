from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    mfa_required: bool = False
    challenge_token: str | None = None


class AuthStatusResponse(BaseModel):
    enabled: bool
    oidc_enabled: bool = False
    oidc_login_url: str | None = None


class OrganizationAccessResponse(BaseModel):
    organization_id: int
    name: str
    slug: str
    role: UserRole
    is_current: bool


class OrganizationSwitchRequest(BaseModel):
    organization_id: int = Field(gt=0)


class AuthSessionResponse(BaseModel):
    id: str
    user_agent: str | None
    client_ip: str | None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    is_current: bool


class MfaChallengeRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=64)


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=64)


class MfaDisableRequest(MfaCodeRequest):
    password: str = Field(min_length=1, max_length=1024)


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaStatusResponse(BaseModel):
    enabled: bool
    recovery_codes_remaining: int


class RecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]
