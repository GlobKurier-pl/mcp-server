import logging
from typing import Any, cast

from fastmcp import FastMCP

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.config.settings import Settings
from globkurier_mcp.infrastructure.mcp.prompts import register_prompts
from globkurier_mcp.infrastructure.mcp.tools.get_countries_tool import (
    get_countries_tool,
)
from globkurier_mcp.infrastructure.mcp.tools.get_product_addons_tool import (
    get_product_addons_tool,
)
from globkurier_mcp.infrastructure.mcp.tools.get_search_url_tool import (
    get_search_url_tool,
)
from globkurier_mcp.infrastructure.mcp.tools.search_products_tool import (
    search_products_tool,
)
from globkurier_mcp.infrastructure.mcp.tools.shipment_status_tool import (
    get_shipment_status_tool,
)

logger = logging.getLogger(__name__)


def create_mcp_server(
    query_bus: QueryBus,
    settings: Settings,
) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        query_bus: Configured query bus for handling queries
        settings: Application settings

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP("globkurier-api-mcp")

    # Note: The 'ping' method is handled automatically by MCP protocol.
    # According to MCP spec (2025-03-26), ping requests must return an empty response {}.
    # The protocol-level implementation is in mcp.server.session.ServerSession.

    @mcp.tool(
        name="get_shipment_status",
        description=(
            "Retrieve detailed shipment tracking status from GlobKurier API. "
            "Returns current status, complete tracking history with timestamps, "
            "sender/receiver addresses, and delivery confirmation. "
            "Supports both Polish and English language responses."
        ),
        tags={"shipping", "tracking", "logistics", "real-time"},
    )
    async def get_shipment_status(order_number: str, language: str | None = None) -> dict[str, Any]:
        """
        Retrieve shipment tracking status from GlobKurier.

        Args:
            order_number: GlobKurier order number (e.g., 'GK160825421616')
            language: Language code - 'pl' or 'en' (default: 'pl')

        Returns:
            Detailed shipment status including tracking history
        """
        return await get_shipment_status_tool(
            query_bus=query_bus,
            order_number=order_number,
            language=language,
        )

    @mcp.tool(
        name="get_countries",
        description=(
            "Fetch the complete list of countries supported by GlobKurier. "
            "Each country entry contains: 'id' (numeric country ID required by other tools), "
            "'name' (country name), 'iso_code' (ISO 3166-1 alpha-2 or regional code), "
            "EU membership status, road transport availability, and postal code formats. "
            "ALWAYS call this tool first to resolve country IDs before calling "
            "search_products, get_product_addons, or get_search_url. "
            "Find the country by name or iso_code, then use its 'id' field value."
        ),
        tags={"shipping", "countries", "reference-data"},
    )
    async def get_countries() -> dict[str, Any]:
        """
        Fetch all countries supported by GlobKurier.

        Returns:
            Dictionary with 'countries' list, each entry containing 'id', 'name', 'iso_code', etc.
        """
        return await get_countries_tool(query_bus=query_bus)

    @mcp.tool(
        name="search_products",
        description=(
            "Search for available shipping products based on package "
            "dimensions, weight, quantity, and country locations. "
            "Returns products from multiple carriers (DPD, InPost, DHL, FedEx, UPS, GLS, etc.) "
            "grouped by delivery time (fast, superfast, noon, morning, standard). "
            "Includes pricing, delivery times, available addons, and carrier details. "
            "IMPORTANT: Do NOT guess or assume country IDs. "
            "Always call get_countries first, "
            "find the matching country by name or ISO code, "
            "and use the value from its 'id' field as the country ID."
        ),
        tags={"shipping", "pricing", "products", "carriers", "search"},
    )
    async def search_products(
        width: int,
        height: int,
        length: int,
        weight: int,
        quantity: int,
        sender_country_id: int,
        receiver_country_id: int,
    ) -> dict[str, Any]:
        """
        Search for available shipping products.

        Args:
            width: Package width in centimeters (cm)
            height: Package height in centimeters (cm)
            length: Package length in centimeters (cm)
            weight: Package weight in kilograms (kg)
            quantity: Number of packages
            sender_country_id: Sender country numeric ID — call get_countries,
                find country by name or ISO code, use its 'id' field value
            receiver_country_id: Receiver country numeric ID — same as sender_country_id

        Returns:
            Products grouped by delivery time with pricing and carrier details
        """
        return await search_products_tool(
            query_bus=query_bus,
            width=width,
            height=height,
            length=length,
            weight=weight,
            quantity=quantity,
            sender_country_id=sender_country_id,
            receiver_country_id=receiver_country_id,
        )

    @mcp.tool(
        name="get_product_addons",
        description=(
            "Get available addons for a specific shipping product. "
            "Returns addons like insurance, cash on delivery (COD), "
            "delivery to company/private person, "
            "non-standard items, and other supplements. "
            "Each addon includes pricing, category, requirements, and validation rules. "
            "Use this after selecting a product from search_products to see available options. "
            "IMPORTANT: Do NOT guess or assume country IDs. "
            "Always call get_countries first, "
            "find the matching country by name or ISO code, "
            "and use the value from its 'id' field as the country ID."
        ),
        tags={"shipping", "addons", "insurance", "cod", "supplements"},
    )
    async def get_product_addons(
        product_id: int,
        length: int,
        width: int,
        height: int,
        weight: int,
        quantity: int,
        sender_country_id: int,
        receiver_country_id: int,
        sender_post_code: str,
        receiver_post_code: str,
        insurance_value: float | None = None,
        insurance_currency: str = "PLN",
        cash_on_delivery_value: float | None = None,
        cash_on_delivery_currency: str = "PLN",
    ) -> dict[str, Any]:
        """
        Get available addons for a shipping product.

        Args:
            product_id: Product ID from search_products result
            length: Package length in centimeters (cm)
            width: Package width in centimeters (cm)
            height: Package height in centimeters (cm)
            weight: Package weight in kilograms (kg)
            quantity: Number of packages
            sender_country_id: Sender country numeric ID — call get_countries,
                find country by name or ISO code, use its 'id' field value
            receiver_country_id: Receiver country numeric ID — same as sender_country_id
            sender_post_code: Sender postal code
            receiver_post_code: Receiver postal code
            insurance_value: Optional insurance value for cost recalculation
            insurance_currency: Insurance currency (default: PLN)
            cash_on_delivery_value: Optional COD value for cost recalculation
            cash_on_delivery_currency: COD currency (default: PLN)

        Returns:
            Available addons with pricing and requirements
        """
        return await get_product_addons_tool(
            query_bus=query_bus,
            product_id=product_id,
            length=length,
            width=width,
            height=height,
            weight=weight,
            quantity=quantity,
            sender_country_id=sender_country_id,
            receiver_country_id=receiver_country_id,
            sender_post_code=sender_post_code,
            receiver_post_code=receiver_post_code,
            insurance_value=insurance_value,
            insurance_currency=insurance_currency,
            cash_on_delivery_value=cash_on_delivery_value,
            cash_on_delivery_currency=cash_on_delivery_currency,
        )

    @mcp.resource(
        uri="globkurier://countries",
        name="GlobKurier Countries",
        description=(
            "Complete list of countries supported by GlobKurier shipping service. "
            "Includes detailed information: EU membership status, road transport availability, "
            "postal code formats, phone prefixes, and regional variations. "
            "Data is cached for optimal performance."
        ),
        mime_type="application/json",
        tags={"shipping", "countries", "reference-data", "cached"},
        meta={
            "cache_ttl_seconds": settings.cache_countries_ttl_seconds,
            "cache_ttl_days": settings.cache_countries_ttl_seconds / 86400,
            "api_version": "v1",
            "data_source": "GlobKurier API",
            "total_countries": "~240",
            "last_updated": "dynamic",
        },
    )
    async def get_countries_resource() -> str:
        """
        List of all available countries for shipping.

        This resource provides a cached list of countries supported by GlobKurier,
        including information about EU membership, transport availability, and postal code formats.

        Cache TTL: Configurable via CACHE_COUNTRIES_TTL_SECONDS (default: 7 days)

        Returns:
            JSON string with countries list
        """
        from globkurier_mcp.application.queries.get_countries import GetCountriesQuery

        try:
            result: Any = await query_bus.execute(GetCountriesQuery())
            return cast(str, result.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to fetch countries: {e}")
            raise

    @mcp.resource(
        uri="globkurier://countries/{iso_code}",
        name="GlobKurier Country by ISO",
        description=(
            "Retrieve detailed information about a specific country by its ISO code. "
            "Supports both standard ISO 3166-1 alpha-2 codes (e.g., 'PL', 'US') and "
            "custom regional codes used by GlobKurier "
            "(e.g., 'GB1' for England, 'ES2' for Spanish islands). "
            "Search is case-insensitive. Data is served from cache for optimal performance."
        ),
        mime_type="application/json",
        tags={"shipping", "countries", "reference-data", "lookup", "cached"},
        meta={
            "cache_ttl_seconds": settings.cache_countries_ttl_seconds,
            "supports_regional_codes": True,
            "case_insensitive": True,
            "examples": ["PL", "US", "GB1", "ES2"],
        },
    )
    async def get_country_by_iso_resource(iso_code: str) -> str:
        """
        Get a specific country by ISO code.

        Args:
            iso_code: ISO 3166-1 alpha-2 code or custom regional code

        Returns:
            JSON string with country details

        Raises:
            ValueError: If country with given ISO code is not found
        """
        from globkurier_mcp.application.queries.get_countries import GetCountryByIsoQuery

        try:
            result: Any = await query_bus.execute(GetCountryByIsoQuery(iso_code=iso_code))
            return cast(str, result.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to fetch country '{iso_code}': {e}")
            raise

    @mcp.tool(
        name="get_search_url",
        description=(
            "Generate a direct link to the GlobKurier search page "
            "with pre-filled shipment parameters. "
            "Use this after presenting a product offer to give the user "
            "a URL to complete the purchase. "
            "Pass the productId of the selected product to highlight "
            "that offer on the search page. "
            "IMPORTANT: whenever the user selects or confirms a specific product, "
            "always call this tool to retrieve the purchase URL and present it to the user. "
            "Do NOT guess or assume country IDs — always call get_countries, "
            "find the country by name or ISO code, "
            "and use the value from its 'id' field."
        ),
        tags={"shipping", "search", "url", "purchase"},
    )
    async def get_search_url(
        width: int,
        height: int,
        length: int,
        weight: int,
        quantity: int,
        sender_country_id: int,
        receiver_country_id: int,
        product_id: int,
    ) -> dict[str, Any]:
        """
        Generate a GlobKurier search page URL.

        Args:
            width: Package width in centimeters (cm)
            height: Package height in centimeters (cm)
            length: Package length in centimeters (cm)
            weight: Package weight in kilograms (kg)
            quantity: Number of packages
            sender_country_id: Sender country numeric ID — call get_countries,
                find country by name or ISO code, use its 'id' field value
            receiver_country_id: Receiver country numeric ID — same as sender_country_id
            product_id: Product ID to pre-select and highlight on the search page

        Returns:
            Dictionary with 'url' key containing the full search URL
        """
        return await get_search_url_tool(
            query_bus=query_bus,
            width=width,
            height=height,
            length=length,
            weight=weight,
            quantity=quantity,
            sender_country_id=sender_country_id,
            receiver_country_id=receiver_country_id,
            product_id=product_id,
        )

    @mcp.tool(
        name="get_search_url",
        description=(
            "Generate a direct link to the GlobKurier search page with pre-filled shipment parameters. "
            "Use this after presenting a product offer to give the user a URL to complete the purchase. "
            "Optionally pass a productId to highlight a specific offer on the search page."
        ),
        tags={"shipping", "search", "url", "purchase"},
    )
    async def get_search_url(
        width: int,
        height: int,
        length: int,
        weight: int,
        quantity: int,
        sender_country_id: int,
        receiver_country_id: int,
        product_id: int | None = None,
    ) -> dict:
        """
        Generate a GlobKurier search page URL.

        Args:
            width: Package width in cm
            height: Package height in cm
            length: Package length in cm
            weight: Package weight in kg
            quantity: Number of packages
            sender_country_id: Sender country ID (e.g., 1 for Poland)
            receiver_country_id: Receiver country ID (e.g., 1 for Poland)
            product_id: Optional product ID to pre-select and highlight on the search page

        Returns:
            Dictionary with 'url' key containing the full search URL
        """
        return await get_search_url_tool(
            query_bus=query_bus,
            width=width,
            height=height,
            length=length,
            weight=weight,
            quantity=quantity,
            sender_country_id=sender_country_id,
            receiver_country_id=receiver_country_id,
            product_id=product_id,
        )

    # Register all assistant prompts (uses QueryBus for CQRS)
    register_prompts(mcp, query_bus, settings)

    return mcp
