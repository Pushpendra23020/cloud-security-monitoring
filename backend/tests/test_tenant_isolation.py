from dataclasses import dataclass
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.security import create_access_token, hash_password
from app.database.models.alert import Alert
from app.database.models.asset import Asset
from app.database.models.audit_log import AuditLog
from app.database.models.cloud_account import CloudAccount
from app.database.models.finding import Finding
from app.database.models.incident import Incident
from app.database.models.organization import Organization, OrganizationMembership
from app.database.models.user import User
from app.database.session import SessionLocal
from app.main import app


client = TestClient(app)


@dataclass(frozen=True)
class Tenant:
    organization_id: int
    user_id: int
    membership_id: int
    username: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def create_tenant(*, role: str = "admin", global_role: str | None = None) -> Tenant:
    suffix = uuid4().hex[:12]
    with SessionLocal() as db:
        organization = Organization(
            name=f"Tenant {suffix}",
            slug=f"tenant-{suffix}",
        )
        user = User(
            username=f"tenant-user-{suffix}",
            email=f"tenant-user-{suffix}@example.com",
            password_hash=hash_password(f"Tenant-secure-{suffix}"),
            role=global_role or role,
        )
        db.add_all([organization, user])
        db.flush()
        membership = OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role=role,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        token = create_access_token(
            user.id,
            user.username,
            membership.role,
            organization.id,
            membership.id,
        )
        return Tenant(
            organization_id=organization.id,
            user_id=user.id,
            membership_id=membership.id,
            username=user.username,
            token=token,
        )


def cleanup_tenants(*tenants: Tenant) -> None:
    organization_ids = [tenant.organization_id for tenant in tenants]
    user_ids = [tenant.user_id for tenant in tenants]
    with SessionLocal() as db:
        asset_ids = list(
            db.scalars(
                Asset.__table__.select()
                .with_only_columns(Asset.id)
                .where(Asset.organization_id.in_(organization_ids))
            )
        )
        if asset_ids:
            db.execute(delete(Finding).where(Finding.asset_id.in_(asset_ids)))
        db.execute(delete(Finding).where(Finding.organization_id.in_(organization_ids)))
        db.execute(delete(Asset).where(Asset.organization_id.in_(organization_ids)))
        db.execute(delete(Alert).where(Alert.organization_id.in_(organization_ids)))
        db.execute(delete(Incident).where(Incident.organization_id.in_(organization_ids)))
        db.execute(delete(CloudAccount).where(CloudAccount.organization_id.in_(organization_ids)))
        db.execute(delete(AuditLog).where(AuditLog.organization_id.in_(organization_ids)))
        db.execute(
            delete(OrganizationMembership).where(
                OrganizationMembership.organization_id.in_(organization_ids)
            )
        )
        db.execute(delete(User).where(User.id.in_(user_ids)))
        db.execute(delete(Organization).where(Organization.id.in_(organization_ids)))
        db.commit()


@pytest.fixture(autouse=True)
def enable_authentication(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)


def account_payload(account_id: str, name: str) -> dict:
    return {
        "name": name,
        "provider": "aws",
        "account_id": account_id,
        "region": "ap-south-1",
    }


def test_cloud_accounts_and_assets_are_isolated_by_tenant():
    tenant_a = create_tenant()
    tenant_b = create_tenant()
    shared_account_id = uuid4().hex[:12]
    try:
        response_a = client.post(
            "/api/v1/cloud-accounts",
            headers=tenant_a.headers,
            json=account_payload(shared_account_id, "Tenant A account"),
        )
        response_b = client.post(
            "/api/v1/cloud-accounts",
            headers=tenant_b.headers,
            json=account_payload(shared_account_id, "Tenant B account"),
        )
        assert response_a.status_code == 201
        assert response_b.status_code == 201
        account_a = response_a.json()
        account_b = response_b.json()

        listed_a = client.get("/api/v1/cloud-accounts", headers=tenant_a.headers)
        assert listed_a.status_code == 200
        assert [item["id"] for item in listed_a.json()] == [account_a["id"]]

        cross_tenant_update = client.patch(
            f"/api/v1/cloud-accounts/{account_b['id']}",
            headers=tenant_a.headers,
            json={"name": "must not change"},
        )
        assert cross_tenant_update.status_code == 404

        shared_asset_id = f"i-{uuid4().hex[:12]}"
        secret_asset_id = f"i-{uuid4().hex[:12]}"
        for headers, account_id in (
            (tenant_a.headers, account_a["id"]),
            (tenant_b.headers, account_b["id"]),
        ):
            response = client.post(
                "/api/v1/assets",
                headers=headers,
                json={
                    "cloud_account_id": account_id,
                    "asset_type": "ec2_instance",
                    "asset_id": shared_asset_id,
                },
            )
            assert response.status_code == 201
        secret_response = client.post(
            "/api/v1/assets",
            headers=tenant_b.headers,
            json={
                "cloud_account_id": account_b["id"],
                "asset_type": "ec2_instance",
                "asset_id": secret_asset_id,
            },
        )
        assert secret_response.status_code == 201

        assets_a = client.get("/api/v1/assets", headers=tenant_a.headers)
        assert assets_a.status_code == 200
        assert {item["asset_id"] for item in assets_a.json()} == {shared_asset_id}
        cross_tenant_asset = client.get(
            f"/api/v1/assets/{secret_asset_id}/risk-explanation",
            headers=tenant_a.headers,
        )
        assert cross_tenant_asset.status_code == 404
    finally:
        cleanup_tenants(tenant_a, tenant_b)


def test_alert_incident_statistics_and_dashboard_are_tenant_scoped():
    tenant_a = create_tenant()
    tenant_b = create_tenant()
    alert_a_id = f"alert-{uuid4().hex}"
    alert_b_id = f"alert-{uuid4().hex}"
    incident_a_id = f"incident-{uuid4().hex}"
    incident_b_id = f"incident-{uuid4().hex}"
    try:
        with SessionLocal() as db:
            db.add_all(
                [
                    Alert(
                        organization_id=tenant_a.organization_id,
                        alert_id=alert_a_id,
                        rule_id="tenant-test",
                        rule_name="Tenant A alert",
                        severity="high",
                        event_id=f"event-{uuid4().hex}",
                        event_name="TestEvent",
                        cloud_provider="aws",
                    ),
                    Alert(
                        organization_id=tenant_b.organization_id,
                        alert_id=alert_b_id,
                        rule_id="tenant-test",
                        rule_name="Tenant B alert",
                        severity="critical",
                        event_id=f"event-{uuid4().hex}",
                        event_name="TestEvent",
                        cloud_provider="aws",
                    ),
                    Incident(
                        organization_id=tenant_a.organization_id,
                        incident_id=incident_a_id,
                        title="Tenant A incident",
                        severity="high",
                        cloud_provider="aws",
                    ),
                    Incident(
                        organization_id=tenant_b.organization_id,
                        incident_id=incident_b_id,
                        title="Tenant B incident",
                        severity="critical",
                        cloud_provider="aws",
                    ),
                ]
            )
            db.commit()

        alerts_a = client.get("/api/v1/alerts", headers=tenant_a.headers)
        assert alerts_a.status_code == 200
        assert [item["alert_id"] for item in alerts_a.json()["items"]] == [alert_a_id]
        assert client.get(
            f"/api/v1/alerts/{alert_b_id}", headers=tenant_a.headers
        ).status_code == 404
        assert client.post(
            f"/api/v1/alerts/{alert_b_id}/acknowledge", headers=tenant_a.headers
        ).status_code == 404

        incidents_a = client.get("/api/v1/incidents", headers=tenant_a.headers)
        assert incidents_a.status_code == 200
        assert [item["incident_id"] for item in incidents_a.json()["items"]] == [
            incident_a_id
        ]
        assert client.get(
            f"/api/v1/incidents/{incident_b_id}", headers=tenant_a.headers
        ).status_code == 404

        statistics = client.get("/api/v1/statistics", headers=tenant_a.headers)
        assert statistics.status_code == 200
        assert statistics.json()["total"] == 1
        assert statistics.json()["high"] == 1
        assert statistics.json()["critical"] == 0

        dashboard = client.get("/api/v1/dashboard/summary", headers=tenant_a.headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["alerts"]["total"] == 1
        assert dashboard.json()["incidents"]["total"] == 1
    finally:
        cleanup_tenants(tenant_a, tenant_b)


def test_membership_role_is_authoritative_and_users_are_scoped():
    viewer = create_tenant(role="viewer", global_role="admin")
    other = create_tenant()
    try:
        forbidden = client.post(
            "/api/v1/cloud-accounts",
            headers=viewer.headers,
            json=account_payload(uuid4().hex[:12], "Forbidden account"),
        )
        assert forbidden.status_code == 403

        own_users = client.get("/api/v1/users", headers=other.headers)
        assert own_users.status_code == 200
        assert [user["id"] for user in own_users.json()] == [other.user_id]
        cross_tenant_change = client.patch(
            f"/api/v1/users/{viewer.user_id}/status",
            headers=other.headers,
            json={"is_active": False},
        )
        assert cross_tenant_change.status_code == 404
    finally:
        cleanup_tenants(viewer, other)


def test_stale_or_mismatched_membership_token_is_rejected():
    tenant = create_tenant()
    try:
        mismatched = create_access_token(
            tenant.user_id,
            tenant.username,
            "admin",
            tenant.organization_id,
            tenant.membership_id + 999_999,
        )
        response = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {mismatched}"},
        )
        assert response.status_code == 401

        with SessionLocal() as db:
            membership = db.get(OrganizationMembership, tenant.membership_id)
            membership.is_active = False
            db.commit()

        response = client.get("/api/v1/dashboard/summary", headers=tenant.headers)
        assert response.status_code == 401
    finally:
        cleanup_tenants(tenant)


def test_database_rejects_cross_tenant_parent_relationships():
    tenant_a = create_tenant()
    tenant_b = create_tenant()
    try:
        with SessionLocal() as db:
            account_b = CloudAccount(
                organization_id=tenant_b.organization_id,
                provider="aws",
                name="Tenant B parent",
                account_id=uuid4().hex[:12],
            )
            db.add(account_b)
            db.commit()
            db.refresh(account_b)

            db.add(
                Asset(
                    organization_id=tenant_a.organization_id,
                    cloud_account_id=account_b.id,
                    asset_type="ec2_instance",
                    asset_id=f"i-{uuid4().hex[:12]}",
                )
            )
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()

            asset_b = Asset(
                organization_id=tenant_b.organization_id,
                cloud_account_id=account_b.id,
                asset_type="ec2_instance",
                asset_id=f"i-{uuid4().hex[:12]}",
            )
            db.add(asset_b)
            db.commit()
            db.refresh(asset_b)

            db.add(
                Finding(
                    organization_id=tenant_a.organization_id,
                    asset_id=asset_b.id,
                    title="Invalid cross-tenant finding",
                    severity="high",
                )
            )
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()
    finally:
        cleanup_tenants(tenant_a, tenant_b)


def test_tenant_scoped_alert_and_incident_identifiers_can_collide():
    tenant_a = create_tenant()
    tenant_b = create_tenant()
    shared_alert_id = f"alert-{uuid4().hex}"
    shared_detection_key = f"detection-{uuid4().hex}"
    shared_fingerprint = f"fingerprint-{uuid4().hex}"
    shared_incident_id = f"incident-{uuid4().hex}"
    try:
        with SessionLocal() as db:
            for tenant in (tenant_a, tenant_b):
                db.add(
                    Alert(
                        organization_id=tenant.organization_id,
                        alert_id=shared_alert_id,
                        rule_id="tenant-collision",
                        rule_name="Tenant-scoped collision",
                        severity="high",
                        event_id=f"event-{tenant.organization_id}",
                        event_name="TestEvent",
                        detection_key=shared_detection_key,
                        fingerprint=shared_fingerprint,
                        cloud_provider="aws",
                    )
                )
                db.add(
                    Incident(
                        organization_id=tenant.organization_id,
                        incident_id=shared_incident_id,
                        title="Tenant-scoped collision",
                        severity="high",
                        cloud_provider="aws",
                    )
                )
            db.commit()

            assert (
                db.query(Alert).filter(Alert.alert_id == shared_alert_id).count()
                == 2
            )
            assert (
                db.query(Incident)
                .filter(Incident.incident_id == shared_incident_id)
                .count()
                == 2
            )
    finally:
        cleanup_tenants(tenant_a, tenant_b)
