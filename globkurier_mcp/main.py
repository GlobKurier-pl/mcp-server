"""Main entrypoint for GlobKurier MCP Server.

This file wires together all layers of the hexagonal architecture:
1. Configuration
2. Infrastructure adapters
3. Application services
4. MCP server
"""

import logging

from globkurier_mcp.application.bus.dispatcher import create_query_bus
from globkurier_mcp.application.queries.get_countries import (
    GetCountriesQueryHandler,
    GetCountryByIsoQueryHandler,
)
from globkurier_mcp.application.queries.get_product_addons import (
    GetProductAddonsQueryHandler,
)
from globkurier_mcp.application.queries.get_prompts import (
    GetAllPromptsQueryHandler,
    GetPromptByNameQueryHandler,
)
from globkurier_mcp.application.queries.get_search_url import (
    GetSearchUrlQueryHandler,
)
from globkurier_mcp.application.queries.get_shipment_status import (
    GetShipmentStatusQueryHandler,
)
from globkurier_mcp.application.queries.search_products import (
    SearchProductsQueryHandler,
)
from globkurier_mcp.config.settings import get_settings
from globkurier_mcp.infrastructure.cache import CachedCountryRepository
from globkurier_mcp.infrastructure.http.countries_client import GlobKurierCountriesClient
from globkurier_mcp.infrastructure.http.globkurier_client import GlobKurierHttpClient
from globkurier_mcp.infrastructure.http.products_client import GlobKurierProductsClient
from globkurier_mcp.infrastructure.logging import setup_logging
from globkurier_mcp.infrastructure.mcp.server import create_mcp_server
from globkurier_mcp.infrastructure.prompts import JsonPromptRepository

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entrypoint - dependency injection and server startup."""
    # 1. Load configuration
    settings = get_settings()

    # 2. Setup logging (must be first!)
    setup_logging(settings)
    logger.info("GlobKurier MCP Server starting...")
    logger.info(
        f"Configuration: host={settings.mcp_host}, port={settings.mcp_port}, "
        f"transport={settings.mcp_transport}"
    )

    # 3. Create infrastructure adapters (implements ports)
    logger.debug("Creating infrastructure adapters...")

    # Shipping adapter
    globkurier_client = GlobKurierHttpClient(settings=settings)

    # Countries adapter with caching
    countries_http_client = GlobKurierCountriesClient(settings=settings)
    countries_repository = CachedCountryRepository(
        repository=countries_http_client,
        ttl_seconds=settings.cache_countries_ttl_seconds,
    )

    # Prompts adapter (JSON-based)
    prompt_repository = JsonPromptRepository()

    # Products adapter
    products_client = GlobKurierProductsClient(settings=settings)

    # 4. Create application layer handlers
    logger.debug("Creating application handlers...")
    get_shipment_status_handler = GetShipmentStatusQueryHandler(
        tracking_port=globkurier_client,
    )
    get_countries_handler = GetCountriesQueryHandler(
        country_repository=countries_repository,
    )
    get_country_by_iso_handler = GetCountryByIsoQueryHandler(
        country_repository=countries_repository,
    )
    get_all_prompts_handler = GetAllPromptsQueryHandler(
        prompt_repository=prompt_repository,
    )
    get_prompt_by_name_handler = GetPromptByNameQueryHandler(
        prompt_repository=prompt_repository,
    )
    search_products_handler = SearchProductsQueryHandler(
        product_search_port=products_client,
    )
    get_product_addons_handler = GetProductAddonsQueryHandler(
        product_addons_port=products_client,
    )
    get_search_url_handler = GetSearchUrlQueryHandler(
        portal_base_url=settings.globkurier_portal_base_url,
    )

    # 5. Create and configure query bus
    logger.debug("Configuring query bus...")
    query_bus = create_query_bus(
        get_shipment_status_handler=get_shipment_status_handler,
        get_countries_handler=get_countries_handler,
        get_country_by_iso_handler=get_country_by_iso_handler,
        get_all_prompts_handler=get_all_prompts_handler,
        get_prompt_by_name_handler=get_prompt_by_name_handler,
        search_products_handler=search_products_handler,
        get_product_addons_handler=get_product_addons_handler,
        get_search_url_handler=get_search_url_handler,
    )

    # 6. Create MCP server
    logger.debug("Creating MCP server...")
    mcp = create_mcp_server(
        query_bus=query_bus,
        settings=settings,
    )

    # 7. Run server
    logger.info(
        f"Starting MCP server on {settings.mcp_host}:{settings.mcp_port} "
        f"(transport: {settings.mcp_transport})"
    )
    mcp.run(
        transport=settings.mcp_transport,
        host=settings.mcp_host,
        port=settings.mcp_port,
        stateless_http=settings.mcp_stateless_http,
    )


if __name__ == "__main__":
    main()
