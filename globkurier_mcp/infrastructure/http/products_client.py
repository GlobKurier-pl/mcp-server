"""HTTP client for product search - implements ProductSearchPort.

This is an infrastructure adapter that implements the domain port interface.
"""

import logging
from decimal import Decimal
from typing import Any

import httpx

from globkurier_mcp.config.settings import Settings
from globkurier_mcp.core.products.models import (
    Addon,
    CollectionTypeOption,
    DeliveryTypeOption,
    GetAddonsForProductCriteria,
    GetAddonsResult,
    Product,
    ProductSearchCriteria,
    ProductSearchResult,
    Transport,
)
from globkurier_mcp.core.products.ports import (
    ProductAddonsError,
    ProductAddonsPort,
    ProductSearchError,
    ProductSearchPort,
)

logger = logging.getLogger(__name__)


class GlobKurierProductsClient(ProductSearchPort, ProductAddonsPort):
    """HTTP client for GlobKurier products API.

    This adapter implements ProductSearchPort and ProductAddonsPort from the domain layer.
    """

    def __init__(self, settings: Settings):
        """Initialize HTTP client.

        Args:
            settings: Application settings with API configuration
        """
        self._base_url = settings.globkurier_api_base_url
        self._log_requests = settings.log_requests

    async def search_products(
        self, criteria: ProductSearchCriteria
    ) -> ProductSearchResult:
        """Search for available shipping products.

        Args:
            criteria: Search criteria with package details

        Returns:
            ProductSearchResult with products grouped by delivery time

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If response cannot be parsed
        """
        url = f"{self._base_url}/v1/products"

        # Build query parameters
        params = self._build_query_params(criteria)

        if self._log_requests:
            logger.info(f"Searching products: {url}?{self._format_params(params)}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)

                if response.status_code == 400:
                    error_body = response.text
                    logger.warning(f"Products API returned 400: {error_body[:500]}")
                    raise ProductSearchError(
                        f"Invalid search parameters: {error_body[:200]}",
                        status_code=400,
                    )

                response.raise_for_status()
                data = response.json()

                if self._log_requests:
                    count = len(data.get("standard", []))
                    logger.info(f"Products search response: {count} standard products")

                return self._map_to_domain(data)

        except ProductSearchError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error searching products: {e.response.status_code}, "
                f"body: {e.response.text[:200]}"
            )
            raise ProductSearchError(
                f"API returned HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                original_error=e,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error searching products: {e}")
            raise ProductSearchError(f"Request failed: {str(e)}", original_error=e) from e
        except Exception as e:
            logger.exception(f"Unexpected error searching products: {e}")
            raise ProductSearchError(f"Unexpected error: {str(e)}", original_error=e) from e

    def _build_query_params(self, criteria: ProductSearchCriteria) -> dict[str, Any]:
        """Build query parameters from search criteria.

        Args:
            criteria: Search criteria

        Returns:
            Dictionary of query parameters
        """
        return {
            "width": criteria.width,
            "height": criteria.height,
            "length": criteria.length,
            "weight": criteria.weight,
            "quantity": criteria.quantity,
            "senderCountryId": criteria.sender_country_id,
            "receiverCountryId": criteria.receiver_country_id,
            "flatList": "true",
        }

    def _format_params(self, params: dict[str, Any]) -> str:
        """Format parameters for logging (truncated).

        Args:
            params: Query parameters

        Returns:
            Formatted string
        """
        parts = []
        for key, value in params.items():
            if isinstance(value, list):
                for v in value:
                    parts.append(f"{key}={v}")
            else:
                parts.append(f"{key}={value}")
        return "&".join(parts[:10])  # Truncate for logging

    def _map_to_domain(self, api_response: dict[str, Any]) -> ProductSearchResult:
        """Map API response to domain model.

        Args:
            api_response: Raw API response

        Returns:
            ProductSearchResult domain model
        """
        return ProductSearchResult(
            fast=tuple(
                self._map_product_to_domain(p) for p in api_response.get("fast", [])
            ),
            superfast=tuple(
                self._map_product_to_domain(p)
                for p in api_response.get("superfast", [])
            ),
            noon=tuple(
                self._map_product_to_domain(p) for p in api_response.get("noon", [])
            ),
            morning=tuple(
                self._map_product_to_domain(p) for p in api_response.get("morning", [])
            ),
            standard=tuple(
                self._map_product_to_domain(p) for p in api_response.get("standard", [])
            ),
        )

    def _map_product_to_domain(self, product_data: dict[str, Any]) -> Product:
        """Map single product from API to domain model.

        Args:
            product_data: Product data from API

        Returns:
            Product domain model
        """
        # Parse transport
        transport_data = product_data.get("transport", {})
        transport = Transport(
            code=transport_data.get("code", ""),
            name=transport_data.get("name", ""),
        )

        # Parse collection type options
        collection_type_options = tuple(
            CollectionTypeOption(
                key=opt.get("key", ""),
                trans=opt.get("trans", ""),
                image=opt.get("image", ""),
            )
            for opt in product_data.get("collectionTypeOptions", [])
        )

        # Parse delivery type options
        delivery_type_options = tuple(
            DeliveryTypeOption(
                key=opt.get("key", ""),
                trans=opt.get("trans", ""),
                image=opt.get("image", ""),
            )
            for opt in product_data.get("deliveryTypeOptions", [])
        )

        return Product(
            id=int(product_data.get("id") or 0),
            name=product_data.get("name", ""),
            carrier_name=product_data.get("carrierName", ""),
            service_code=product_data.get("serviceCode"),
            net_price=Decimal(str(product_data.get("netPrice", 0))),
            gross_price=Decimal(str(product_data.get("grossPrice", 0))),
            net_price_standard=(
                Decimal(str(product_data.get("netPriceStandard")))
                if product_data.get("netPriceStandard") is not None
                else None
            ),
            gross_price_standard=(
                Decimal(str(product_data.get("grossPriceStandard")))
                if product_data.get("grossPriceStandard") is not None
                else None
            ),
            currency=product_data.get("currency", "PLN"),
            units=product_data.get("units", 1),
            protocol_available=product_data.get("protocolAvailable", False),
            package_type=product_data.get("packageType", ""),
            package_name=product_data.get("packageName", ""),
            transport=transport,
            for_company=product_data.get("forCompany", False),
            carrier_logo_link=product_data.get("carrierLogoLink", ""),
            discount_code_allowed=product_data.get("discountCodeAllowed", False),
            average_delivery=product_data.get("averageDelivery"),
            delivery_time_type=product_data.get("deliveryTimeType", "STANDARD"),
            details_link=product_data.get("detailsLink"),
            promo=product_data.get("promo"),
            has_country_zone_routing=product_data.get("hasCountryZoneRouting", False),
            on_demand_delivery_point_required=product_data.get(
                "onDemandDeliveryPointRequired", False
            ),
            custom_document_type=product_data.get("customDocumentType"),
            labels=tuple(product_data.get("labels", [])),
            collection_types=tuple(product_data.get("collectionTypes", [])),
            delivery_types=tuple(product_data.get("deliveryTypes", [])),
            addons_categories=tuple(product_data.get("addonsCategories", [])),
            collection_type_options=collection_type_options,
            delivery_type_options=delivery_type_options,
            carrier_id=product_data.get("carrierId", 0),
        )

    async def get_addons_for_product(
        self, criteria: GetAddonsForProductCriteria
    ) -> GetAddonsResult:
        """Get available addons for a product.

        Args:
            criteria: Criteria with product ID and package details

        Returns:
            GetAddonsResult with available addons

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If response cannot be parsed
        """
        url = f"{self._base_url}/v1/product/addons"

        # Build query parameters
        params = self._build_addons_query_params(criteria)

        if self._log_requests:
            logger.info(f"Getting addons for product: {url}?{self._format_params(params)}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)

                if response.status_code == 400:
                    error_body = response.text
                    logger.warning(f"Addons API returned 400: {error_body[:500]}")
                    raise ProductAddonsError(
                        f"Invalid addon request parameters: {error_body[:200]}",
                        status_code=400,
                    )

                response.raise_for_status()
                data = response.json()

                if self._log_requests:
                    logger.info(f"Addons response: {len(data.get('addons', []))} addons found")

                return self._map_addons_to_domain(data)

        except ProductAddonsError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching addons: {e.response.status_code}, "
                f"body: {e.response.text[:200]}"
            )
            raise ProductAddonsError(
                f"API returned HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                original_error=e,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching addons: {e}")
            raise ProductAddonsError(f"Request failed: {str(e)}", original_error=e) from e
        except Exception as e:
            logger.exception(f"Unexpected error fetching addons: {e}")
            raise ProductAddonsError(f"Unexpected error: {str(e)}", original_error=e) from e

    def _build_addons_query_params(
        self, criteria: GetAddonsForProductCriteria
    ) -> dict[str, Any]:
        """Build query parameters for addons request.

        Args:
            criteria: Get addons criteria

        Returns:
            Dictionary of query parameters
        """
        params = {
            "productId": criteria.product_id,
            "length": criteria.length,
            "width": criteria.width,
            "height": criteria.height,
            "weight": criteria.weight,
            "quantity": criteria.quantity,
            "senderCountryId": criteria.sender_country_id,
            "receiverCountryId": criteria.receiver_country_id,
            "senderPostCode": criteria.sender_post_code,
            "receiverPostCode": criteria.receiver_post_code,
        }

        # Add optional insurance parameters
        if criteria.insurance_value is not None:
            params["insuranceValue"] = float(criteria.insurance_value)
            params["insuranceCurrency"] = criteria.insurance_currency

        # Add optional COD parameters
        if criteria.cash_on_delivery_value is not None:
            params["cashOnDeliveryValue"] = float(criteria.cash_on_delivery_value)
            params["cashOnDeliveryCurrency"] = criteria.cash_on_delivery_currency

        return params

    def _map_addons_to_domain(self, api_response: dict[str, Any]) -> GetAddonsResult:
        """Map API response to domain model.

        Args:
            api_response: Raw API response

        Returns:
            GetAddonsResult domain model
        """
        addons_data = api_response.get("addons", [])
        addons = tuple(self._map_addon_to_domain(addon) for addon in addons_data)

        # Map requiredAlternativeAddonsGroups
        groups_data = api_response.get("requiredAlternativeAddonsGroups", [])
        required_groups = tuple(tuple(group) for group in groups_data)

        return GetAddonsResult(
            addons=addons, required_alternative_addons_groups=required_groups
        )

    def _map_addon_to_domain(self, addon_data: dict[str, Any]) -> Addon:
        """Map single addon from API to domain model.

        Args:
            addon_data: Addon data from API

        Returns:
            Addon domain model
        """
        return Addon(
            id=int(addon_data.get("id") or 0),
            addon_name=addon_data.get("addonName", ""),
            description=addon_data.get("description"),
            attributes=addon_data.get("attributes"),
            addon_logo=addon_data.get("addonLogo"),
            price=Decimal(str(addon_data.get("price", 0))),
            price_gross=Decimal(str(addon_data.get("priceGross", 0))),
            price_description=addon_data.get("priceDescription"),
            quantity=addon_data.get("quantity", 1),
            currency=addon_data.get("currency", "PLN"),
            category=addon_data.get("category", ""),
            is_required=addon_data.get("isRequired", False),
            insurance_required=addon_data.get("insuranceRequired", False),
            min_value=(
                Decimal(str(addon_data.get("minValue")))
                if addon_data.get("minValue") is not None
                else None
            ),
            max_value=(
                Decimal(str(addon_data.get("maxValue")))
                if addon_data.get("maxValue") is not None
                else None
            ),
            value_currency=addon_data.get("valueCurrency"),
            days_to_return=addon_data.get("daysToReturn"),
            verification_required=addon_data.get("verificationRequired", False),
            in_price=addon_data.get("inPrice", True),
        )
