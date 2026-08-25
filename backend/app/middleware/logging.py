import time
import uuid

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.responses import Response

from app.utils.logger import get_logger
from app.utils.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)


logger = get_logger(__name__)


def _metric_path(request: Request) -> str:
    """
    Return a bounded Prometheus path label.

    After FastAPI routing has completed, scope["route"].path
    contains the route template, for example:

        /api/v1/alerts/{alert_id}

    rather than the concrete URL containing an ID.
    """
    route = request.scope.get("route")

    route_path = getattr(
        route,
        "path",
        None,
    )

    if route_path:
        return str(route_path)

    # Fallback mainly covers unmatched/404 requests.
    return request.url.path


class RequestLoggingMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        started_at = time.perf_counter()

        request_id = (
            request.headers.get("X-Request-ID")
            or uuid.uuid4().hex
        )

        request.state.request_id = request_id

        method = request.method

        # Do not instrument the Prometheus scrape itself.
        record_metrics = (
            request.url.path != "/metrics"
        )

        if record_metrics:
            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method,
            ).inc()

        try:
            response = await call_next(
                request
            )

        except Exception:
            duration_seconds = (
                time.perf_counter()
                - started_at
            )

            metric_path = _metric_path(
                request
            )

            if record_metrics:
                HTTP_REQUESTS_TOTAL.labels(
                    method=method,
                    path=metric_path,
                    status_code="500",
                ).inc()

                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=method,
                    path=metric_path,
                ).observe(
                    duration_seconds
                )

            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": round(
                        duration_seconds * 1000,
                        3,
                    ),
                    "client_ip": (
                        request.client.host
                        if request.client
                        else None
                    ),
                },
            )

            raise

        else:
            duration_seconds = (
                time.perf_counter()
                - started_at
            )

            metric_path = _metric_path(
                request
            )

            if record_metrics:
                HTTP_REQUESTS_TOTAL.labels(
                    method=method,
                    path=metric_path,
                    status_code=str(
                        response.status_code
                    ),
                ).inc()

                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=method,
                    path=metric_path,
                ).observe(
                    duration_seconds
                )

            response.headers[
                "X-Request-ID"
            ] = request_id

            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": request.url.path,
                    "status_code": (
                        response.status_code
                    ),
                    "duration_ms": round(
                        duration_seconds * 1000,
                        3,
                    ),
                    "client_ip": (
                        request.client.host
                        if request.client
                        else None
                    ),
                },
            )

            return response

        finally:
            if record_metrics:
                HTTP_REQUESTS_IN_PROGRESS.labels(
                    method=method,
                ).dec()
