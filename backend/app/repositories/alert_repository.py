from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.alert import Alert


class AlertRepository(ABC):
    @abstractmethod
    def save(
        self,
        alert: Alert,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        alert: Alert,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def load_all(
        self,
    ) -> List[Alert]:
        raise NotImplementedError

    @abstractmethod
    def list_alerts(
        self,
        *,
        severity: str | None = None,
        status: str | None = None,
        cloud_provider: str | None = None,
        account_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[List[Alert], int]:
        raise NotImplementedError

    @abstractmethod
    def get_statistics(
        self,
    ) -> dict[str, int]:
        raise NotImplementedError

    @abstractmethod
    def get_by_incident_id(
        self,
        incident_id: str,
    ) -> List[Alert]:
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        alert_id: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def detection_exists(
        self,
        detection_key: str,
    ) -> bool:
        raise NotImplementedError
