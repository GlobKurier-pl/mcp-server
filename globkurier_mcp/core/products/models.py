"""Domain models for product search.

This module contains value objects and aggregates for the products bounded context.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Transport:
    """Transport information value object."""

    code: str
    name: str


@dataclass(frozen=True)
class CollectionTypeOption:
    """Collection type option value object."""

    key: str
    trans: str
    image: str


@dataclass(frozen=True)
class DeliveryTypeOption:
    """Delivery type option value object."""

    key: str
    trans: str
    image: str


@dataclass(frozen=True)
class Product:
    """Product value object - represents a single shipping product.

    This is an immutable domain model representing a product returned
    from the GlobKurier API.
    """

    id: int
    name: str
    carrier_name: str
    service_code: str | None
    net_price: Decimal
    gross_price: Decimal
    currency: str
    units: int
    package_type: str
    package_name: str
    transport: Transport
    average_delivery: int | None
    delivery_time_type: str
    carrier_logo_link: str
    details_link: str | None
    labels: tuple[str, ...]
    collection_types: tuple[str, ...]
    delivery_types: tuple[str, ...]
    addons_categories: tuple[str, ...]
    collection_type_options: tuple[CollectionTypeOption, ...]
    delivery_type_options: tuple[DeliveryTypeOption, ...]
    carrier_id: int
    # Optional fields
    net_price_standard: Decimal | None = None
    gross_price_standard: Decimal | None = None
    protocol_available: bool = False
    for_company: bool = False
    discount_code_allowed: bool = False
    promo: str | None = None
    has_country_zone_routing: bool = False
    on_demand_delivery_point_required: bool = False
    custom_document_type: str | None = None

    def __post_init__(self) -> None:
        """Validate product data."""
        if self.id <= 0:
            raise ValueError("Product ID must be positive")
        if not self.name:
            raise ValueError("Product name cannot be empty")
        if not self.carrier_name:
            raise ValueError("Carrier name cannot be empty")
        if self.net_price < 0:
            raise ValueError("Net price cannot be negative")
        if self.gross_price < 0:
            raise ValueError("Gross price cannot be negative")


@dataclass(frozen=True)
class ProductSearchCriteria:
    """Search criteria value object."""

    # Package dimensions
    width: int
    height: int
    length: int
    weight: int
    quantity: int

    # Location
    sender_country_id: int
    receiver_country_id: int

    def __post_init__(self) -> None:
        """Validate search criteria."""
        if self.width <= 0:
            raise ValueError("Width must be positive")
        if self.height <= 0:
            raise ValueError("Height must be positive")
        if self.length <= 0:
            raise ValueError("Length must be positive")
        if self.weight <= 0:
            raise ValueError("Weight must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.sender_country_id <= 0:
            raise ValueError("Sender country ID must be positive")
        if self.receiver_country_id <= 0:
            raise ValueError("Receiver country ID must be positive")


@dataclass(frozen=True)
class ProductSearchResult:
    """Aggregate root for product search results.

    Groups products by delivery time type.
    """

    fast: tuple[Product, ...]
    superfast: tuple[Product, ...]
    noon: tuple[Product, ...]
    morning: tuple[Product, ...]
    standard: tuple[Product, ...]

    def get_all_products(self) -> tuple[Product, ...]:
        """Get all products from all categories."""
        return (
            self.fast
            + self.superfast
            + self.noon
            + self.morning
            + self.standard
        )

    def get_total_count(self) -> int:
        """Get total number of products."""
        return len(self.get_all_products())

    def get_cheapest_product(self) -> Product | None:
        """Get the cheapest product (by gross price)."""
        all_products = self.get_all_products()
        if not all_products:
            return None
        return min(all_products, key=lambda p: p.gross_price)

    def get_fastest_product(self) -> Product | None:
        """Get the fastest product (by average delivery time)."""
        all_products = self.get_all_products()
        if not all_products:
            return None

        # Filter out products without delivery time
        with_delivery = [p for p in all_products if p.average_delivery is not None]
        if not with_delivery:
            return None

        return min(with_delivery, key=lambda p: p.average_delivery)  # type: ignore


@dataclass(frozen=True)
class Addon:
    """Addon value object - represents a product addon/supplement.

    This is an immutable domain model representing an addon that can be
    added to a shipping product.
    """

    id: int
    addon_name: str
    category: str
    price: Decimal
    price_gross: Decimal
    currency: str
    is_required: bool
    insurance_required: bool
    in_price: bool
    quantity: int = 1
    description: str | None = None
    attributes: dict[str, Any] | None = None
    addon_logo: str | None = None
    price_description: str | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    value_currency: str | None = None
    days_to_return: int | None = None
    verification_required: bool = False

    def __post_init__(self) -> None:
        """Validate addon data."""
        if self.id <= 0:
            raise ValueError("Addon ID must be positive")
        if not self.addon_name:
            raise ValueError("Addon name cannot be empty")
        if not self.category:
            raise ValueError("Category cannot be empty")
        if self.price < 0:
            raise ValueError("Net price cannot be negative")
        if self.price_gross < 0:
            raise ValueError("Gross price cannot be negative")


@dataclass(frozen=True)
class GetAddonsForProductCriteria:
    """Criteria for getting product addons value object."""

    # Product identification
    product_id: int

    # Package dimensions (required)
    length: int
    width: int
    height: int
    weight: int
    quantity: int

    # Location (required)
    sender_country_id: int
    receiver_country_id: int
    sender_post_code: str
    receiver_post_code: str

    # Optional insurance and COD parameters
    insurance_value: Decimal | None = None
    insurance_currency: str = "PLN"
    cash_on_delivery_value: Decimal | None = None
    cash_on_delivery_currency: str = "PLN"

    def __post_init__(self) -> None:
        """Validate criteria."""
        if self.product_id <= 0:
            raise ValueError("Product ID must be positive")
        if self.length <= 0:
            raise ValueError("Length must be positive")
        if self.width <= 0:
            raise ValueError("Width must be positive")
        if self.height <= 0:
            raise ValueError("Height must be positive")
        if self.weight <= 0:
            raise ValueError("Weight must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.sender_country_id <= 0:
            raise ValueError("Sender country ID must be positive")
        if self.receiver_country_id <= 0:
            raise ValueError("Receiver country ID must be positive")
        if not self.sender_post_code:
            raise ValueError("Sender post code cannot be empty")
        if not self.receiver_post_code:
            raise ValueError("Receiver post code cannot be empty")

        # Business rule: Insurance value must be >= COD value
        if (
            self.insurance_value is not None
            and self.cash_on_delivery_value is not None
            and self.insurance_value < self.cash_on_delivery_value
        ):
            raise ValueError(
                "Insurance value must be greater than or equal to cash on delivery value"
            )


@dataclass(frozen=True)
class GetAddonsResult:
    """Aggregate root for product addons result."""

    addons: tuple[Addon, ...]
    required_alternative_addons_groups: tuple[tuple[int, ...], ...] = ()

    def get_required_addons(self) -> tuple[Addon, ...]:
        """Get only required addons."""
        return tuple(addon for addon in self.addons if addon.is_required)

    def get_optional_addons(self) -> tuple[Addon, ...]:
        """Get only optional addons."""
        return tuple(addon for addon in self.addons if not addon.is_required)

    def get_addons_by_category(self, category: str) -> tuple[Addon, ...]:
        """Get addons filtered by category."""
        return tuple(addon for addon in self.addons if addon.category == category)

    def has_category(self, category: str) -> bool:
        """Check if any addon from given category exists."""
        return any(addon.category == category for addon in self.addons)
