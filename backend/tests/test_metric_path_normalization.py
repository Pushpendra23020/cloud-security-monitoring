from types import SimpleNamespace

from starlette.requests import Request

from app.middleware.logging import (
    _metric_path,
)


def build_request(
    path: str,
    route_path: str | None = None,
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "root_path": "",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
    }

    if route_path is not None:
        scope["route"] = SimpleNamespace(
            path=route_path,
        )

    return Request(scope)


def test_metric_path_uses_route_template():
    request = build_request(
        "/api/v1/alerts/abc123",
        "/api/v1/alerts/{alert_id}",
    )

    assert _metric_path(request) == (
        "/api/v1/alerts/{alert_id}"
    )


def test_metric_path_falls_back_to_request_path():
    request = build_request(
        "/does-not-exist"
    )

    assert _metric_path(request) == (
        "/does-not-exist"
    )
