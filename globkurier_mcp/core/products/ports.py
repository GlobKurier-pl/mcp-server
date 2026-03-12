"""Ports (interfaces) for product search.

This module defines abstract interfaces that infrastructure must implement.
"""

from abc import ABC, abstractmethod

from globkurier_mcp.core.products.models import (
    GetAddonsForProductCriteria,
    GetAddonsResult,
    ProductSearchCriteria,
    ProductSearchResult,
)


class ProductSearchError(Exception):
    """Raised when product search fails (e.g. invalid params, API error)."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(message)


class ProductAddonsError(Exception):
    """Raised when fetching product addons fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(message)


class ProductSearchPort(ABC):
    """Abstract interface for product search operations.

    This port defines what operations the domain needs for searching products.
    Infrastructure layer must implement this interface.
    """

    @abstractmethod
    async def search_products(
        self, criteria: ProductSearchCriteria
    ) -> ProductSearchResult:
        """Search for available shipping products.

        Args:
            criteria: Search criteria with package details and locations

        Returns:
            ProductSearchResult with products grouped by delivery time type

        Raises:
            Exception: If products cannot be searched
        """
        pass


class ProductAddonsPort(ABC):
    """Abstract interface for product addons operations.

    This port defines what operations the domain needs for getting product addons.
    Infrastructure layer must implement this interface.
    """

    @abstractmethod
    async def get_addons_for_product(
        self, criteria: GetAddonsForProductCriteria
    ) -> GetAddonsResult:
        """Get available addons for a specific product.

        Args:
            criteria: Criteria with product ID, package details, and locations

        Returns:
            GetAddonsResult with available addons for the product

        Raises:
            Exception: If addons cannot be retrieved
        """
        pass
