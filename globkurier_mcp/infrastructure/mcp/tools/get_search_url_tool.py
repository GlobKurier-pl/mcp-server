"""MCP tool for generating GlobKurier search page URL.

Returns a direct link to the GlobKurier search page pre-filled with
shipment parameters, allowing the user to complete the purchase.
"""

import logging
from typing import Any, cast

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.application.queries.get_search_url import GetSearchUrlQuery

logger = logging.getLogger(__name__)


async def get_search_url_tool(
    query_bus: QueryBus,
    width: int,
    height: int,
    length: int,
    weight: int,
    quantity: int,
    sender_country_id: int,
    receiver_country_id: int,
    product_id: int,
) -> dict[str, Any]:
    """Generate a GlobKurier search page URL with pre-filled parameters.

    Args:
        query_bus: Query bus for executing queries
        width: Package width in centimeters (cm)
        height: Package height in centimeters (cm)
        length: Package length in centimeters (cm)
        weight: Package weight in kilograms (kg)
        quantity: Number of packages
        sender_country_id: Sender country numeric ID (call get_countries to resolve)
        receiver_country_id: Receiver country numeric ID (call get_countries to resolve)
        product_id: Product ID to pre-select on the search page

    Returns:
        Dictionary with the search URL

    Raises:
        RuntimeError: When URL generation fails
    """
    query = GetSearchUrlQuery(
        width=width,
        height=height,
        length=length,
        weight=weight,
        quantity=quantity,
        sender_country_id=sender_country_id,
        receiver_country_id=receiver_country_id,
        product_id=product_id,
    )

    try:
        result: Any = await query_bus.execute(query)
        return cast(dict[str, Any], result.model_dump())
    except Exception as e:
        logger.error(f"Error in get_search_url_tool: {e}")
        return {"error": True, "code": "UNKNOWN_ERROR", "message": str(e)}
