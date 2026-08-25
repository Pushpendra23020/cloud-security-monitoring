import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.config import settings


class JsonFormatter(logging.Formatter):
    """Format application log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "logger": record.name,
            "message": record.getMessage(),
        }

        optional_fields = (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
        )

        for field in optional_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            default=str,
            separators=(",", ":"),
        )


def configure_logging() -> None:
    """Configure root application logging."""

    root_logger = logging.getLogger()

    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(
        getattr(
            logging,
            settings.LOG_LEVEL.upper(),
            logging.INFO,
        )
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
