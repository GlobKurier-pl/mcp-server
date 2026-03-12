"""MCP tool for searching shipping products.

This tool allows searching for available shipping products based on package
dimensions, weight, and locations.
"""

import logging
from typing import Any, cast

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.application.queries.search_products import SearchProductsQuery
from globkurier_mcp.core.products.ports import ProductSearchError

logger = logging.getLogger(__name__)


async def search_products_tool(
    query_bus: QueryBus,
    width: int,
    height: int,
    length: int,
    weight: int,
    quantity: int,
    sender_country_id: int,
    receiver_country_id: int,
) -> dict[str, Any]:
    """Search for available shipping products.

    Args:
        query_bus: Query bus for executing queries
        width: Package width in centimeters (cm)
        height: Package height in centimeters (cm)
        length: Package length in centimeters (cm)
        weight: Package weight in kilograms (kg)
        quantity: Number of packages
        sender_country_id: Sender country numeric ID (call get_countries to resolve)
        receiver_country_id: Receiver country numeric ID (call get_countries to resolve)

    Returns:
        Dictionary with search results

    Raises:
        ValueError: When search parameters are invalid (e.g. API returned 400)
        RuntimeError: When the product search service fails
    """
    query = SearchProductsQuery(
        width=width,
        height=height,
        length=length,
        weight=weight,
        quantity=quantity,
        sender_country_id=sender_country_id,
        receiver_country_id=receiver_country_id,
    )

    try:
        result: Any = await query_bus.execute(query)
        return cast(dict[str, Any], result.model_dump(by_alias=True))
    except ProductSearchError as e:
        status = f" (HTTP {e.status_code})" if e.status_code else ""
        logger.warning(f"Product search failed{status}: {e}")
        if e.status_code == 400:
            return {"error": True, "code": "INVALID_PARAMS", "message": str(e)}
        return {"error": True, "code": "SERVICE_ERROR", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in search_products_tool: {e}")
        return {"error": True, "code": "UNKNOWN_ERROR", "message": str(e)}
