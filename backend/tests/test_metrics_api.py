from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_metrics_endpoint_available():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert (
        "text/plain"
        in response.headers["content-type"]
    )


def test_metrics_include_app_information():
    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "cloud_security_app_info" in body


def test_http_request_counter_is_exposed():
    client.get("/health")

    response = client.get("/metrics")

    assert (
        "cloud_security_http_requests_total"
        in response.text
    )


def test_http_duration_histogram_is_exposed():
    client.get("/health")

    response = client.get("/metrics")

    assert (
        "cloud_security_http_request_duration_seconds"
        in response.text
    )


def test_http_in_progress_gauge_is_exposed():
    response = client.get("/metrics")

    assert (
        "cloud_security_http_requests_in_progress"
        in response.text
    )
