"""MCP tool for getting product addons.

This tool allows retrieving available addons for a specific shipping product.
"""

import logging
from decimal import Decimal
from typing import Any, cast

from globkurier_mcp.application.bus.dispatcher import QueryBus
from globkurier_mcp.application.queries.get_product_addons import GetProductAddonsQuery
from globkurier_mcp.core.products.ports import ProductAddonsError

logger = logging.getLogger(__name__)


async def get_product_addons_tool(
    query_bus: QueryBus,
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
    """Get available addons for a shipping product.

    Args:
        query_bus: Query bus for executing queries
        product_id: Product ID from search_products result
        length: Package length in centimeters (cm)
        width: Package width in centimeters (cm)
        height: Package height in centimeters (cm)
        weight: Package weight in kilograms (kg)
        quantity: Number of packages
        sender_country_id: Sender country numeric ID (call get_countries to resolve)
        receiver_country_id: Receiver country numeric ID (call get_countries to resolve)
        sender_post_code: Sender postal code
        receiver_post_code: Receiver postal code
        insurance_value: Optional insurance value for cost recalculation
        insurance_currency: Insurance currency (default: PLN)
        cash_on_delivery_value: Optional COD value for cost recalculation
        cash_on_delivery_currency: COD currency (default: PLN)

    Returns:
        Dictionary with addons information

    Raises:
        ValueError: When addon request parameters are invalid (e.g. API returned 400)
        RuntimeError: When the addons service fails
    """
    insurance_decimal = (
        Decimal(str(insurance_value)) if insurance_value is not None else None
    )
    cod_decimal = (
        Decimal(str(cash_on_delivery_value))
        if cash_on_delivery_value is not None
        else None
    )

    query = GetProductAddonsQuery(
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
        insurance_value=insurance_decimal,
        insurance_currency=insurance_currency,
        cash_on_delivery_value=cod_decimal,
        cash_on_delivery_currency=cash_on_delivery_currency,
    )

    try:
        result: Any = await query_bus.execute(query)
        return cast(dict[str, Any], result.model_dump(by_alias=True))
    except ProductAddonsError as e:
        status = f" (HTTP {e.status_code})" if e.status_code else ""
        logger.warning(f"Get addons failed{status}: {e}")
        if e.status_code == 400:
            return {"error": True, "code": "INVALID_PARAMS", "message": str(e)}
        return {"error": True, "code": "SERVICE_ERROR", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_product_addons_tool: {e}")
        return {"error": True, "code": "UNKNOWN_ERROR", "message": str(e)}
