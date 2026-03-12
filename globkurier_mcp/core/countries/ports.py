"""Ports (interfaces) for countries bounded context."""

from abc import ABC, abstractmethod

from globkurier_mcp.core.countries.models import Country


class CountryRepositoryPort(ABC):
    """Port for accessing country data.

    This is the interface that the domain expects.
    Infrastructure adapters will implement this.
    """

    @abstractmethod
    async def get_all_countries(self) -> list[Country]:
        """Retrieve all available countries.

        Returns:
            List of all countries
        """
        ...


class CountryRepositoryError(Exception):
    """Base exception for country repository errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
