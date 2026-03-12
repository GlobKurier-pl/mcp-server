"""Test script for product addons functionality."""

import asyncio
from decimal import Decimal

from globkurier_mcp.application.queries.get_product_addons import (
    GetProductAddonsQuery,
    GetProductAddonsQueryHandler,
)
from globkurier_mcp.config.settings import Settings
from globkurier_mcp.infrastructure.http.products_client import GlobKurierProductsClient
from globkurier_mcp.infrastructure.logging import setup_logging


async def test_get_product_addons():
    """Test product addons with real API."""
    # Setup
    settings = Settings(
        globkurier_api_base_url="https://api.globkurier.pl",
        log_level="INFO",
        log_requests=True,
    )
    setup_logging(settings)

    print("\n" + "=" * 80)
    print("TESTING GET PRODUCT ADDONS")
    print("=" * 80)

    # Create infrastructure
    products_client = GlobKurierProductsClient(settings=settings)

    # Create handler
    handler = GetProductAddonsQueryHandler(product_addons_port=products_client)

    # Create query (using a product ID from previous search)
    # You need to get this from search_products first
    query = GetProductAddonsQuery(
        product_id=605,  # Example product ID - replace with actual one
        width=1,
        height=1,
        length=1,
        weight=1,
        quantity=1,
        sender_country_id=1,  # Poland
        receiver_country_id=1,  # Poland
        sender_post_code="01-001",
        receiver_post_code="41-100",
        insurance_value=Decimal("500"),
        insurance_currency="PLN",
        cash_on_delivery_value=Decimal("400"),
        cash_on_delivery_currency="PLN",
    )

    print("\nQuery parameters:")
    print(f"  Product ID: {query.product_id}")
    print(f"  Package: {query.width}x{query.height}x{query.length} cm, {query.weight} kg")
    print(f"  From: Country {query.sender_country_id}, {query.sender_post_code}")
    print(f"  To: Country {query.receiver_country_id}, {query.receiver_post_code}")
    print(f"  Insurance: {query.insurance_value} {query.insurance_currency}")
    print(f"  COD: {query.cash_on_delivery_value} {query.cash_on_delivery_currency}")

    # Execute query
    print("\n" + "-" * 80)
    print("Getting product addons...")
    print("-" * 80)

    try:
        result = await handler.handle(query)

        # Display results
        print("\nResults:")
        print(f"  Total addons: {result.total_addons}")
        print(f"  Required: {result.required_addons_count}")
        print(f"  Optional: {result.optional_addons_count}")

        # Display all addons
        if result.addons:
            print("\n" + "-" * 80)
            print("Available Addons:")
            print("-" * 80)
            for i, addon in enumerate(result.addons, 1):
                print(f"\n{i}. {addon.addon_name}")
                print(f"   Category: {addon.category}")
                print(f"   Price: {addon.price}")
                if addon.price_description:
                    print(f"   Price description: {addon.price_description}")
                print(f"   Required: {'Yes' if addon.is_required else 'No'}")
                if addon.description:
                    print(f"   Description: {addon.description}")
                if addon.min_value is not None:
                    print(f"   Min value: {addon.min_value}")
                if addon.max_value is not None:
                    print(f"   Max value: {addon.max_value}")
                if addon.days_to_return is not None:
                    print(f"   Days to return: {addon.days_to_return}")
                print(f"   Verification required: {'Yes' if addon.verification_required else 'No'}")

        print("\n" + "=" * 80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_product_addons())
