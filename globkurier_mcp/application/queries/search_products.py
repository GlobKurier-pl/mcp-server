"""Query for searching shipping products.

This module implements CQRS pattern for product search operations.
"""

import logging
from dataclasses import dataclass

from globkurier_mcp.application.dto.product_dto import (
    CollectionTypeOptionDto,
    DeliveryTypeOptionDto,
    ProductDto,
    ProductSearchResultDto,
    TransportDto,
)
from globkurier_mcp.core.products.models import (
    Product,
    ProductSearchCriteria,
    ProductSearchResult,
)
from globkurier_mcp.core.products.ports import ProductSearchPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchProductsQuery:
    """Query to search for available shipping products.

    Attributes:
        width: Package width in cm
        height: Package height in cm
        length: Package length in cm
        weight: Package weight in kg
        quantity: Number of packages
        sender_country_id: Sender country ID
        receiver_country_id: Receiver country ID
    """

    width: int
    height: int
    length: int
    weight: int
    quantity: int
    sender_country_id: int
    receiver_country_id: int


class SearchProductsQueryHandler:
    """Handler for SearchProductsQuery.

    Follows CQRS pattern - separates query handling from business logic.
    Uses dependency injection to receive product search port.
    """

    def __init__(self, product_search_port: ProductSearchPort):
        """Initialize handler with product search port.

        Args:
            product_search_port: Implementation of ProductSearchPort
        """
        self._product_search_port = product_search_port

    async def handle(self, query: SearchProductsQuery) -> ProductSearchResultDto:
        """Handle the query by searching for products.

        Args:
            query: The query to handle

        Returns:
            ProductSearchResultDto with search results

        Raises:
            ValueError: If search criteria is invalid
            Exception: If product search fails
        """
        logger.debug(
            f"Handling SearchProductsQuery: "
            f"weight={query.weight}kg, "
            f"sender={query.sender_country_id}, "
            f"receiver={query.receiver_country_id}"
        )

        # Create domain search criteria
        criteria = ProductSearchCriteria(
            width=query.width,
            height=query.height,
            length=query.length,
            weight=query.weight,
            quantity=query.quantity,
            sender_country_id=query.sender_country_id,
            receiver_country_id=query.receiver_country_id,
        )

        # Delegate to port (dependency inversion)
        result = await self._product_search_port.search_products(criteria)

        logger.info(
            f"Found {result.get_total_count()} products "
            f"(fast:{len(result.fast)}, superfast:{len(result.superfast)}, "
            f"noon:{len(result.noon)}, morning:{len(result.morning)}, "
            f"standard:{len(result.standard)})"
        )

        # Map domain model to DTO
        return self._map_to_dto(result)

    def _map_to_dto(self, result: ProductSearchResult) -> ProductSearchResultDto:
        """Map domain model to DTO.

        Args:
            result: Domain ProductSearchResult

        Returns:
            ProductSearchResultDto for API response
        """
        # Get cheapest and fastest products
        cheapest = result.get_cheapest_product()
        fastest = result.get_fastest_product()

        return ProductSearchResultDto(
            fast=[self._map_product_to_dto(p) for p in result.fast],
            superfast=[self._map_product_to_dto(p) for p in result.superfast],
            noon=[self._map_product_to_dto(p) for p in result.noon],
            morning=[self._map_product_to_dto(p) for p in result.morning],
            standard=[self._map_product_to_dto(p) for p in result.standard],
            totalProducts=result.get_total_count(),
            cheapestProductId=cheapest.id if cheapest else None,
            fastestProductId=fastest.id if fastest else None,
        )

    def _map_product_to_dto(self, product: Product) -> ProductDto:
        """Map domain Product to DTO.

        Args:
            product: Domain Product model

        Returns:
            ProductDto for API response
        """
        return ProductDto(
            id=product.id,
            name=product.name,
            carrierName=product.carrier_name,
            serviceCode=product.service_code,
            netPrice=product.net_price,
            grossPrice=product.gross_price,
            netPriceStandard=product.net_price_standard,
            grossPriceStandard=product.gross_price_standard,
            currency=product.currency,
            units=product.units,
            protocolAvailable=product.protocol_available,
            packageType=product.package_type,
            packageName=product.package_name,
            transport=TransportDto(
                code=product.transport.code,
                name=product.transport.name,
            ),
            forCompany=product.for_company,
            carrierLogoLink=product.carrier_logo_link,
            discountCodeAllowed=product.discount_code_allowed,
            averageDelivery=product.average_delivery,
            deliveryTimeType=product.delivery_time_type,
            detailsLink=product.details_link,
            promo=product.promo,
            hasCountryZoneRouting=product.has_country_zone_routing,
            onDemandDeliveryPointRequired=product.on_demand_delivery_point_required,
            customDocumentType=product.custom_document_type,
            labels=list(product.labels),
            collectionTypes=list(product.collection_types),
            addonsCategories=list(product.addons_categories),
            deliveryTypes=list(product.delivery_types),
            collectionTypeOptions=[
                CollectionTypeOptionDto(
                    key=opt.key,
                    trans=opt.trans,
                    image=opt.image,
                )
                for opt in product.collection_type_options
            ],
            deliveryTypeOptions=[
                DeliveryTypeOptionDto(
                    key=opt.key,
                    trans=opt.trans,
                    image=opt.image,
                )
                for opt in product.delivery_type_options
            ],
            carrierId=product.carrier_id,
        )
