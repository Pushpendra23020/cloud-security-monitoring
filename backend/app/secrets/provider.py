"""Secret-store boundary for deployment-specific implementations."""

import os
from abc import ABC, abstractmethod


class SecretProvider(ABC):
    @abstractmethod
    def get(self, reference: str) -> str | None:
        """Return a secret without logging or serializing it."""


class EnvironmentSecretProvider(SecretProvider):
    """Development/container provider; production can replace this with Vault or a cloud store."""

    def get(self, reference: str) -> str | None:
        return os.getenv(reference)
