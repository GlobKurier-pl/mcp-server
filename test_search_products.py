"""Test script for product search functionality."""

import asyncio

from globkurier_mcp.application.queries.search_products import (
    SearchProductsQuery,
    SearchProductsQueryHandler,
)
from globkurier_mcp.config.settings import Settings
from globkurier_mcp.infrastructure.http.products_client import GlobKurierProductsClient
from globkurier_mcp.infrastructure.logging import setup_logging


async def test_search_products():
    """Test product search with real API."""
    # Setup
    settings = Settings(
        globkurier_api_base_url="https://api.globkurier.pl",
        log_level="INFO",
        log_requests=True,
    )
    setup_logging(settings)

    print("\n" + "=" * 80)
    print("TESTING PRODUCT SEARCH")
    print("=" * 80)

    # Create infrastructure
    products_client = GlobKurierProductsClient(settings=settings)

    # Create handler
    handler = SearchProductsQueryHandler(product_search_port=products_client)

    # Create query (matching your example)
    query = SearchProductsQuery(
        width=1,
        height=1,
        length=1,
        weight=1,
        quantity=1,
        sender_country_id=1,  # Poland
        receiver_country_id=1,  # Poland
        sender_post_code="01-001",
        receiver_post_code="41-100",
        package_type="PARCEL",
        transport_type="ROAD",
        collection_types=("PICKUP",),
        delivery_types=("PICKUP",),
    )

    print("\nSearch criteria:")
    print(f"  Package: {query.width}x{query.height}x{query.length} cm, {query.weight} kg")
    print(f"  From: Country {query.sender_country_id}, {query.sender_post_code}")
    print(f"  To: Country {query.receiver_country_id}, {query.receiver_post_code}")
    print(f"  Type: {query.package_type}, Transport: {query.transport_type}")
    print(f"  Collection: {query.collection_types}, Delivery: {query.delivery_types}")

    # Execute query
    print("\n" + "-" * 80)
    print("Searching products...")
    print("-" * 80)

    result = await handler.handle(query)

    # Display results
    print("\nResults:")
    print(f"  Total products: {result.total_products}")
    print(f"  Fast: {len(result.fast)}")
    print(f"  Superfast: {len(result.superfast)}")
    print(f"  Noon: {len(result.noon)}")
    print(f"  Morning: {len(result.morning)}")
    print(f"  Standard: {len(result.standard)}")

    if result.cheapest_product_id:
        print(f"\n  Cheapest product ID: {result.cheapest_product_id}")
    if result.fastest_product_id:
        print(f"  Fastest product ID: {result.fastest_product_id}")

    # Display first 5 standard products
    if result.standard:
        print("\n" + "-" * 80)
        print("Top 5 Standard Products:")
        print("-" * 80)
        for i, product in enumerate(result.standard[:5], 1):
            print(f"\n{i}. {product.name}")
            print(f"   Carrier: {product.carrier_name}")
            print(f"   Price: {product.gross_price} {product.currency} (net: {product.net_price})")
            print(f"   Delivery: {product.average_delivery} days ({product.delivery_time_type})")
            print(f"   Collection: {', '.join(product.collection_types)}")
            print(f"   Delivery types: {', '.join(product.delivery_types)}")
            print(f"   Product ID: {product.id}")

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_search_products())
