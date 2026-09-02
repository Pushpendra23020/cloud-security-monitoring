from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import settings
from app.core.security import decode_access_token, hash_password
from app.database.models.audit_log import AuditLog
from app.database.models.organization import Organization, OrganizationMembership
from app.database.models.user import User
from app.database.session import SessionLocal
from app.main import app
from app.repositories.organization_repository import OrganizationRepository


client = TestClient(app)


def create_user() -> tuple[User, str]:
    suffix = uuid4().hex[:10]
    password = f"Organization-secure-{suffix}"
    with SessionLocal() as db:
        user = User(
            username=f"org-switch-{suffix}",
            email=f"org-switch-{suffix}@example.com",
            password_hash=hash_password(password),
            role="admin",
        )
        db.add(user)
        db.flush()
        db.add(
            OrganizationMembership(
                organization_id=1,
                user_id=user.id,
                role="admin",
            )
        )
        db.commit()
        db.refresh(user)
        db.expunge(user)
    return user, password


def login(user: User, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_organization(name: str = "Secondary Workspace") -> Organization:
    with SessionLocal() as db:
        organization = Organization(
            name=name,
            slug=f"workspace-{uuid4().hex}",
        )
        db.add(organization)
        db.commit()
        db.refresh(organization)
        db.expunge(organization)
    return organization


def add_membership(
    user_id: int,
    organization_id: int,
    *,
    role: str = "viewer",
    is_active: bool = True,
) -> OrganizationMembership:
    with SessionLocal() as db:
        membership = OrganizationMembership(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            is_active=is_active,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        db.expunge(membership)
    return membership


def cleanup(user: User, *organization_ids: int) -> None:
    with SessionLocal() as db:
        db.execute(delete(AuditLog).where(AuditLog.user == user.username))
        db.execute(
            delete(OrganizationMembership).where(
                OrganizationMembership.user_id == user.id
            )
        )
        db.execute(delete(User).where(User.id == user.id))
        if organization_ids:
            db.execute(
                delete(Organization).where(Organization.id.in_(organization_ids))
            )
        db.commit()


def test_member_can_list_and_switch_organizations(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user()
    organization = create_organization()
    try:
        token = login(user, password)
        target_membership = add_membership(
            user.id,
            organization.id,
            role="viewer",
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/auth/organizations", headers=headers)
        assert response.status_code == 200
        target = next(
            item
            for item in response.json()
            if item["organization_id"] == organization.id
        )
        assert target["role"] == "viewer"
        assert target["is_current"] is False

        response = client.post(
            "/api/v1/auth/switch-organization",
            headers=headers,
            json={"organization_id": organization.id},
        )
        assert response.status_code == 200
        switched_token = response.json()["access_token"]
        payload = decode_access_token(switched_token)
        assert payload["org_id"] == organization.id
        assert payload["membership_id"] == target_membership.id

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {switched_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["role"] == "viewer"
    finally:
        cleanup(user, organization.id)


def test_non_member_cannot_switch_organizations(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user()
    organization = create_organization("Unrelated Workspace")
    try:
        token = login(user, password)
        response = client.post(
            "/api/v1/auth/switch-organization",
            headers={"Authorization": f"Bearer {token}"},
            json={"organization_id": organization.id},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Active organization membership required."
    finally:
        cleanup(user, organization.id)


def test_inactive_member_cannot_switch_organizations(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user()
    organization = create_organization("Inactive Workspace")
    try:
        token = login(user, password)
        add_membership(
            user.id,
            organization.id,
            is_active=False,
        )
        headers = {"Authorization": f"Bearer {token}"}

        list_response = client.get(
            "/api/v1/auth/organizations",
            headers=headers,
        )
        assert list_response.status_code == 200
        assert organization.id not in {
            item["organization_id"] for item in list_response.json()
        }

        response = client.post(
            "/api/v1/auth/switch-organization",
            headers=headers,
            json={"organization_id": organization.id},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Active organization membership required."
    finally:
        cleanup(user, organization.id)


def test_viewer_can_switch_back_to_an_admin_organization(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user()
    viewer_organization = create_organization("Viewer Workspace")
    try:
        login_token = login(user, password)
        add_membership(user.id, viewer_organization.id, role="viewer")
        switch_to_viewer = client.post(
            "/api/v1/auth/switch-organization",
            headers={"Authorization": f"Bearer {login_token}"},
            json={"organization_id": viewer_organization.id},
        )
        assert switch_to_viewer.status_code == 200

        viewer_token = switch_to_viewer.json()["access_token"]
        switch_back = client.post(
            "/api/v1/auth/switch-organization",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"organization_id": 1},
        )
        assert switch_back.status_code == 200
        payload = decode_access_token(switch_back.json()["access_token"])
        assert payload["org_id"] == 1
        assert payload["role"] == "admin"
    finally:
        cleanup(user, viewer_organization.id)
