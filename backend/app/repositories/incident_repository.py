from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.incident import Incident


class IncidentRepository(ABC):
    @abstractmethod
    def save(
        self,
        incident: Incident,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        incident: Incident,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_incidents(
        self,
    ) -> List[Incident]:
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        incident_id: str,
    ) -> bool:
        raise NotImplementedError
