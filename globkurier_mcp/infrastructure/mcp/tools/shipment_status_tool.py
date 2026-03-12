import logging
from typing import Any, cast

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.application.queries.get_shipment_status import GetShipmentStatusQuery
from globkurier_mcp.core.shipping.ports import ShipmentNotFoundError, TrackingServiceError

logger = logging.getLogger(__name__)


async def get_shipment_status_tool(
    query_bus: QueryBus,
    order_number: str,
    language: str | None = None,
) -> dict[str, Any]:
    """MCP tool for retrieving shipment status.

    This is the adapter between MCP and our application layer.
    It delegates to the query bus rather than calling infrastructure directly.

    Args:
        query_bus: The query bus to dispatch queries
        order_number: GlobKurier order number (e.g., 'GK160825421616')
        language: Language code ('pl' or 'en')

    Returns:
        Shipment status as dictionary (serialized DTO) or error dict with
        keys: error (bool), code (str), message (str)
    """
    query = GetShipmentStatusQuery(
        order_number=order_number,
        language=language or "pl",
    )

    try:
        result_dto: Any = await query_bus.execute(query)
        return cast(dict[str, Any], result_dto.model_dump())
    except ShipmentNotFoundError as e:
        logger.warning(f"Shipment not found: {order_number}")
        return {"error": True, "code": "NOT_FOUND", "message": str(e)}
    except TrackingServiceError as e:
        logger.error(f"Tracking service error for {order_number}: {e}")
        return {"error": True, "code": "SERVICE_ERROR", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error retrieving shipment status for {order_number}: {e}")
        return {"error": True, "code": "UNKNOWN_ERROR", "message": str(e)}
