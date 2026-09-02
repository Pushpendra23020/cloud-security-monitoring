from dataclasses import dataclass

from app.database.models.user import User


DEFAULT_ORGANIZATION_ID = 1


@dataclass(frozen=True)
class TenantContext:
    user: User
    organization_id: int
    role: str
    membership_id: int
    session_id: str | None = None
