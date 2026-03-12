"""Query for getting product addons.

This module implements CQRS pattern for product addons operations.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal

from globkurier_mcp.application.dto.product_dto import AddonDto, GetAddonsResultDto
from globkurier_mcp.core.products.models import (
    Addon,
    GetAddonsForProductCriteria,
    GetAddonsResult,
)
from globkurier_mcp.core.products.ports import ProductAddonsPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetProductAddonsQuery:
    """Query to get available addons for a product.

    Attributes:
        product_id: Product ID from /products endpoint
        length: Package length in cm
        width: Package width in cm
        height: Package height in cm
        weight: Package weight in kg
        quantity: Number of packages
        sender_country_id: Sender country ID
        receiver_country_id: Receiver country ID
        sender_post_code: Sender postal code
        receiver_post_code: Receiver postal code
        insurance_value: Optional insurance value for cost recalculation
        insurance_currency: Insurance currency (default: PLN)
        cash_on_delivery_value: Optional COD value for cost recalculation
        cash_on_delivery_currency: COD currency (default: PLN)
    """

    product_id: int
    length: int
    width: int
    height: int
    weight: int
    quantity: int
    sender_country_id: int
    receiver_country_id: int
    sender_post_code: str
    receiver_post_code: str
    insurance_value: Decimal | None = None
    insurance_currency: str = "PLN"
    cash_on_delivery_value: Decimal | None = None
    cash_on_delivery_currency: str = "PLN"


class GetProductAddonsQueryHandler:
    """Handler for GetProductAddonsQuery.

    Follows CQRS pattern - separates query handling from business logic.
    Uses dependency injection to receive product addons port.
    """

    def __init__(self, product_addons_port: ProductAddonsPort):
        """Initialize handler with product addons port.

        Args:
            product_addons_port: Implementation of ProductAddonsPort
        """
        self._product_addons_port = product_addons_port

    async def handle(self, query: GetProductAddonsQuery) -> GetAddonsResultDto:
        """Handle the query by getting product addons.

        Args:
            query: The query to handle

        Returns:
            GetAddonsResultDto with available addons

        Raises:
            ValueError: If query criteria is invalid
            Exception: If addons retrieval fails
        """
        logger.debug(
            f"Handling GetProductAddonsQuery: "
            f"product_id={query.product_id}, "
            f"weight={query.weight}kg, "
            f"sender={query.sender_country_id}, "
            f"receiver={query.receiver_country_id}"
        )

        # Create domain criteria
        criteria = GetAddonsForProductCriteria(
            product_id=query.product_id,
            length=query.length,
            width=query.width,
            height=query.height,
            weight=query.weight,
            quantity=query.quantity,
            sender_country_id=query.sender_country_id,
            receiver_country_id=query.receiver_country_id,
            sender_post_code=query.sender_post_code,
            receiver_post_code=query.receiver_post_code,
            insurance_value=query.insurance_value,
            insurance_currency=query.insurance_currency,
            cash_on_delivery_value=query.cash_on_delivery_value,
            cash_on_delivery_currency=query.cash_on_delivery_currency,
        )

        # Delegate to port (dependency inversion)
        result = await self._product_addons_port.get_addons_for_product(criteria)

        logger.info(
            f"Found {len(result.addons)} addons for product {query.product_id} "
            f"(required: {len(result.get_required_addons())}, "
            f"optional: {len(result.get_optional_addons())})"
        )

        # Map domain model to DTO
        return self._map_to_dto(result)

    def _map_to_dto(self, result: GetAddonsResult) -> GetAddonsResultDto:
        """Map domain model to DTO.

        Args:
            result: Domain GetAddonsResult

        Returns:
            GetAddonsResultDto for API response
        """
        return GetAddonsResultDto(
            addons=[self._map_addon_to_dto(addon) for addon in result.addons],
            requiredAlternativeAddonsGroups=[
                list(group) for group in result.required_alternative_addons_groups
            ],
            totalAddons=len(result.addons),
            requiredAddonsCount=len(result.get_required_addons()),
            optionalAddonsCount=len(result.get_optional_addons()),
        )

    def _map_addon_to_dto(self, addon: Addon) -> AddonDto:
        """Map domain Addon to DTO.

        Args:
            addon: Domain Addon model

        Returns:
            AddonDto for API response
        """
        return AddonDto(
            id=addon.id,
            addonName=addon.addon_name,
            description=addon.description,
            attributes=addon.attributes,
            addonLogo=addon.addon_logo,
            price=addon.price,
            priceGross=addon.price_gross,
            priceDescription=addon.price_description,
            quantity=addon.quantity,
            currency=addon.currency,
            category=addon.category,
            isRequired=addon.is_required,
            insuranceRequired=addon.insurance_required,
            minValue=addon.min_value,
            maxValue=addon.max_value,
            valueCurrency=addon.value_currency,
            daysToReturn=addon.days_to_return,
            verificationRequired=addon.verification_required,
            inPrice=addon.in_price,
        )
