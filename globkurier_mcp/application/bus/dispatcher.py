from collections.abc import Callable
from typing import Any, TypeVar, cast

from globkurier_mcp.application.queries.get_countries import (
    GetCountriesQuery,
    GetCountriesQueryHandler,
    GetCountryByIsoQuery,
    GetCountryByIsoQueryHandler,
)
from globkurier_mcp.application.queries.get_product_addons import (
    GetProductAddonsQuery,
    GetProductAddonsQueryHandler,
)
from globkurier_mcp.application.queries.get_prompts import (
    GetAllPromptsQuery,
    GetAllPromptsQueryHandler,
    GetPromptByNameQuery,
    GetPromptByNameQueryHandler,
)
from globkurier_mcp.application.queries.get_search_url import (
    GetSearchUrlQuery,
    GetSearchUrlQueryHandler,
)
from globkurier_mcp.application.queries.get_shipment_status import (
    GetShipmentStatusQuery,
    GetShipmentStatusQueryHandler,
)
from globkurier_mcp.application.queries.search_products import (
    SearchProductsQuery,
    SearchProductsQueryHandler,
)

TQuery = TypeVar("TQuery")
TResult = TypeVar("TResult")


class QueryBus:
    """Simple query bus implementing CQRS pattern.

    Routes queries to their respective handlers.
    In a larger application, this could be replaced with a more
    sophisticated implementation (e.g., using dependency injection).
    """

    def __init__(self) -> None:
        self._handlers: dict[type, Callable[[Any], Any]] = {}

    def register(self, query_type: type[TQuery], handler: Callable[[TQuery], TResult]) -> None:
        """Register a query handler.

        Args:
            query_type: The type of query this handler processes
            handler: The handler function/method
        """
        self._handlers[query_type] = handler

    async def execute(self, query: TQuery) -> TResult:
        """Execute a query by dispatching to registered handler.

        Args:
            query: The query to execute

        Returns:
            The result from the handler

        Raises:
            ValueError: If no handler is registered for this query type
        """
        query_type = type(query)
        handler = self._handlers.get(query_type)

        if handler is None:
            raise ValueError(f"No handler registered for query type: {query_type.__name__}")

        return cast(TResult, await handler(query))


def create_query_bus(
    get_shipment_status_handler: GetShipmentStatusQueryHandler,
    get_countries_handler: GetCountriesQueryHandler,
    get_country_by_iso_handler: GetCountryByIsoQueryHandler,
    get_all_prompts_handler: GetAllPromptsQueryHandler,
    get_prompt_by_name_handler: GetPromptByNameQueryHandler,
    search_products_handler: SearchProductsQueryHandler,
    get_product_addons_handler: GetProductAddonsQueryHandler,
    get_search_url_handler: GetSearchUrlQueryHandler,
) -> QueryBus:
    """Factory function to create and configure the query bus.

    Args:
        get_shipment_status_handler: Handler for shipment status queries
        get_countries_handler: Handler for countries list queries
        get_country_by_iso_handler: Handler for single country by ISO code queries
        get_all_prompts_handler: Handler for all prompts queries
        get_prompt_by_name_handler: Handler for single prompt by name queries
        search_products_handler: Handler for product search queries
        get_product_addons_handler: Handler for product addons queries
        get_search_url_handler: Handler for search URL generation queries

    Returns:
        Configured QueryBus instance
    """
    bus = QueryBus()
    bus.register(GetShipmentStatusQuery, get_shipment_status_handler.handle)
    bus.register(GetCountriesQuery, get_countries_handler.handle)
    bus.register(GetCountryByIsoQuery, get_country_by_iso_handler.handle)
    bus.register(GetAllPromptsQuery, get_all_prompts_handler.handle)
    bus.register(GetPromptByNameQuery, get_prompt_by_name_handler.handle)
    bus.register(SearchProductsQuery, search_products_handler.handle)
    bus.register(GetProductAddonsQuery, get_product_addons_handler.handle)
    bus.register(GetSearchUrlQuery, get_search_url_handler.handle)
    return bus
