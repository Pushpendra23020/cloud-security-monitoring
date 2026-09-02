from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_public_responses_include_browser_security_headers(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    response = TestClient(app).get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "strict-transport-security" not in response.headers


def test_api_responses_are_not_cacheable(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    response = TestClient(app).get("/api/v1/auth/status")

    assert response.headers["cache-control"] == "no-store"
