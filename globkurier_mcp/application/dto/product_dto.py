"""DTOs for product search results.

These DTOs are used to transfer data from application layer to presentation layer (MCP).
Domain models are never exposed directly.
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TransportDto(BaseModel):
    """Transport information DTO."""

    code: str
    name: str


class CollectionTypeOptionDto(BaseModel):
    """Collection type option DTO."""

    key: str
    trans: str
    image: str


class DeliveryTypeOptionDto(BaseModel):
    """Delivery type option DTO."""

    key: str
    trans: str
    image: str


class ProductDto(BaseModel):
    """Product DTO for API responses."""

    id: int
    name: str
    carrier_name: str = Field(alias="carrierName")
    service_code: str | None = Field(alias="serviceCode")
    net_price: Decimal = Field(alias="netPrice")
    gross_price: Decimal = Field(alias="grossPrice")
    net_price_standard: Decimal | None = Field(None, alias="netPriceStandard")
    gross_price_standard: Decimal | None = Field(None, alias="grossPriceStandard")
    currency: str
    units: int
    protocol_available: bool = Field(alias="protocolAvailable")
    package_type: str = Field(alias="packageType")
    package_name: str = Field(alias="packageName")
    transport: TransportDto
    for_company: bool = Field(alias="forCompany")
    carrier_logo_link: str = Field(alias="carrierLogoLink")
    discount_code_allowed: bool = Field(alias="discountCodeAllowed")
    average_delivery: int | None = Field(alias="averageDelivery")
    delivery_time_type: str = Field(alias="deliveryTimeType")
    details_link: str | None = Field(alias="detailsLink")
    promo: str | None = None
    has_country_zone_routing: bool = Field(alias="hasCountryZoneRouting")
    on_demand_delivery_point_required: bool = Field(
        alias="onDemandDeliveryPointRequired"
    )
    custom_document_type: str | None = Field(None, alias="customDocumentType")
    labels: list[str]
    collection_types: list[str] = Field(alias="collectionTypes")
    addons_categories: list[str] = Field(alias="addonsCategories")
    delivery_types: list[str] = Field(alias="deliveryTypes")
    collection_type_options: list[CollectionTypeOptionDto] = Field(
        alias="collectionTypeOptions"
    )
    delivery_type_options: list[DeliveryTypeOptionDto] = Field(
        alias="deliveryTypeOptions"
    )
    carrier_id: int = Field(alias="carrierId")

    model_config = ConfigDict(populate_by_name=True)


class ProductSearchResultDto(BaseModel):
    """DTO for product search results grouped by delivery time."""

    fast: list[ProductDto]
    superfast: list[ProductDto]
    noon: list[ProductDto]
    morning: list[ProductDto]
    standard: list[ProductDto]
    total_products: int = Field(alias="totalProducts")
    cheapest_product_id: int | None = Field(None, alias="cheapestProductId")
    fastest_product_id: int | None = Field(None, alias="fastestProductId")

    model_config = ConfigDict(populate_by_name=True)


class AddonDto(BaseModel):
    """Addon DTO for API responses."""

    id: int
    addon_name: str = Field(alias="addonName")
    description: str | None = None
    attributes: dict[str, Any] | None = None
    addon_logo: str | None = Field(None, alias="addonLogo")
    price: Decimal
    price_gross: Decimal = Field(alias="priceGross")
    price_description: str | None = Field(None, alias="priceDescription")
    quantity: int = 1
    currency: str
    category: str
    is_required: bool = Field(alias="isRequired")
    insurance_required: bool = Field(alias="insuranceRequired")
    min_value: Decimal | None = Field(None, alias="minValue")
    max_value: Decimal | None = Field(None, alias="maxValue")
    value_currency: str | None = Field(None, alias="valueCurrency")
    days_to_return: int | None = Field(None, alias="daysToReturn")
    verification_required: bool = Field(alias="verificationRequired")
    in_price: bool = Field(alias="inPrice")

    model_config = ConfigDict(populate_by_name=True)


class GetAddonsResultDto(BaseModel):
    """DTO for product addons result."""

    addons: list[AddonDto]
    required_alternative_addons_groups: list[list[int]] = Field(
        alias="requiredAlternativeAddonsGroups"
    )
    total_addons: int = Field(alias="totalAddons")
    required_addons_count: int = Field(alias="requiredAddonsCount")
    optional_addons_count: int = Field(alias="optionalAddonsCount")

    model_config = ConfigDict(populate_by_name=True)


class SearchUrlDto(BaseModel):
    """DTO for GlobKurier search page URL."""

    url: str = Field(..., description="URL to GlobKurier search page with pre-filled parameters")
