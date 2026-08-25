from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import settings
from app.core.security import hash_password
from app.database.models.audit_log import AuditLog
from app.database.models.user import User
from app.database.session import SessionLocal
from app.main import app

client = TestClient(app)


def create_user(role: str = "admin") -> tuple[User, str]:
    suffix = uuid4().hex[:10]
    password = f"Phase10-secure-{suffix}"
    with SessionLocal() as db:
        user = User(
            username=f"phase10-{suffix}",
            email=f"phase10-{suffix}@example.com",
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
    return user, password


def cleanup(*user_ids: int) -> None:
    with SessionLocal() as db:
        usernames = [
            user.username
            for user in db.query(User).filter(User.id.in_(user_ids)).all()
        ]
        if usernames:
            db.execute(delete(AuditLog).where(AuditLog.user.in_(usernames)))
        db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()


def login(user: User, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_status_is_public(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


def test_login_and_current_user(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("analyst")
    try:
        token = login(user, password)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == user.username
        assert response.json()["role"] == "analyst"
    finally:
        cleanup(user.id)


def test_protected_api_rejects_missing_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


def test_admin_can_create_user_and_action_is_audited(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    admin, password = create_user("admin")
    created_id = None
    try:
        token = login(admin, password)
        suffix = uuid4().hex[:10]
        response = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": f"analyst-{suffix}",
                "email": f"analyst-{suffix}@example.com",
                "password": f"Analyst-secure-{suffix}",
                "role": "analyst",
            },
        )
        assert response.status_code == 201
        created_id = response.json()["id"]
        with SessionLocal() as db:
            audit = db.query(AuditLog).filter_by(
                user=admin.username,
                action="POST /api/v1/users",
            ).one()
            assert audit.status_code == 201
    finally:
        cleanup(*(value for value in (admin.id, created_id) if value is not None))


def test_non_admin_cannot_manage_users(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("viewer")
    try:
        token = login(user, password)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
    finally:
        cleanup(user.id)


def test_non_admin_cannot_create_cloud_accounts(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("analyst")
    try:
        token = login(user, password)
        response = client.post(
            "/api/v1/cloud-accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "provider": "aws",
                "account_id": "123456789012",
                "region": "ap-south-1",
            },
        )
        assert response.status_code == 403
    finally:
        cleanup(user.id)


def test_non_admin_cannot_invoke_aws_management(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    user, password = create_user("analyst")
    try:
        token = login(user, password)
        response = client.get(
            "/api/v1/aws/identity",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
    finally:
        cleanup(user.id)
