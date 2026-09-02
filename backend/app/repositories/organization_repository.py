from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.tenancy import DEFAULT_ORGANIZATION_ID
from app.database.models.organization import Organization, OrganizationMembership
from app.database.models.user import User


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, organization_id: int) -> Organization | None:
        return self.db.get(Organization, organization_id)

    def get_membership(
        self,
        user_id: int,
        organization_id: int,
        *,
        active_only: bool = True,
    ) -> OrganizationMembership | None:
        statement = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
        )
        if active_only:
            statement = statement.where(OrganizationMembership.is_active.is_(True))
        return self.db.scalar(statement)

    def get_default_membership(self, user_id: int) -> OrganizationMembership | None:
        return self.db.scalar(
            select(OrganizationMembership)
            .join(Organization, Organization.id == OrganizationMembership.organization_id)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_active.is_(True),
                Organization.is_active.is_(True),
            )
            .order_by(OrganizationMembership.id)
        )

    def list_active_memberships(
        self,
        user_id: int,
    ) -> list[tuple[Organization, OrganizationMembership]]:
        return list(
            self.db.execute(
                select(Organization, OrganizationMembership)
                .join(
                    OrganizationMembership,
                    OrganizationMembership.organization_id == Organization.id,
                )
                .where(
                    OrganizationMembership.user_id == user_id,
                    OrganizationMembership.is_active.is_(True),
                    Organization.is_active.is_(True),
                )
                .order_by(Organization.name, Organization.id)
            ).all()
        )

    def ensure_default_organization(self) -> Organization:
        organization = self.get(DEFAULT_ORGANIZATION_ID)
        if organization is None:
            organization = Organization(
                id=DEFAULT_ORGANIZATION_ID,
                name="Default Organization",
                slug="default",
            )
            self.db.add(organization)
            self.db.flush()
        return organization

    def ensure_default_membership(
        self,
        user: User,
        *,
        role: str | None = None,
        reactivate: bool = False,
    ) -> OrganizationMembership:
        self.ensure_default_organization()
        membership = self.get_membership(
            user.id,
            DEFAULT_ORGANIZATION_ID,
            active_only=False,
        )
        if membership is None:
            membership = OrganizationMembership(
                organization_id=DEFAULT_ORGANIZATION_ID,
                user_id=user.id,
                role=role or user.role,
                is_active=True,
            )
            self.db.add(membership)
            self.db.commit()
            self.db.refresh(membership)
        elif reactivate:
            membership.role = role or membership.role
            membership.is_active = True
            self.db.commit()
            self.db.refresh(membership)
        return membership

    def list_users(self, organization_id: int) -> list[User]:
        return list(
            self.db.scalars(
                select(User)
                .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
                .where(
                    OrganizationMembership.organization_id == organization_id,
                    OrganizationMembership.is_active.is_(True),
                )
                .order_by(User.username)
            ).all()
        )

    def list_members(
        self,
        organization_id: int,
    ) -> list[tuple[User, OrganizationMembership]]:
        return list(
            self.db.execute(
                select(User, OrganizationMembership)
                .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
                .where(OrganizationMembership.organization_id == organization_id)
                .order_by(User.username)
            ).all()
        )

    def count_active_admins(self, organization_id: int) -> int:
        return int(
            self.db.scalar(
                select(func.count(OrganizationMembership.id)).where(
                    OrganizationMembership.organization_id == organization_id,
                    OrganizationMembership.role == "admin",
                    OrganizationMembership.is_active.is_(True),
                )
            )
            or 0
        )

    def add_membership(self, user: User, organization_id: int, role: str) -> OrganizationMembership:
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user.id,
            role=role,
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership
