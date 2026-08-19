from abc import ABC, abstractmethod

from app.models.alert import Alert


class AlertNotifier(ABC):

    @abstractmethod
    def send(
        self,
        alert: Alert,
    ) -> bool:
        raise NotImplementedError
