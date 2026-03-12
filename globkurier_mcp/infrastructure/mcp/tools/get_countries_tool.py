"""MCP tool for fetching countries list.

This tool exposes the countries data as a callable tool rather than a resource,
improving compatibility with agents that have trouble accessing MCP resources.
"""

import logging
from typing import Any, cast

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.application.queries.get_countries import GetCountriesQuery

logger = logging.getLogger(__name__)


async def get_countries_tool(
    query_bus: QueryBus,
) -> dict[str, Any]:
    """Fetch the complete list of countries supported by GlobKurier.

    Returns:
        Dictionary with countries list including id, name, iso_code and other fields
    """
    try:
        result: Any = await query_bus.execute(GetCountriesQuery())
        return cast(dict[str, Any], result.model_dump())
    except Exception as e:
        logger.error(f"Unexpected error in get_countries_tool: {e}")
        return {"error": True, "code": "UNKNOWN_ERROR", "message": str(e)}