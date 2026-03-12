"""Test script for countries resource."""

import asyncio
import json

from globkurier_mcp.application.queries.get_countries import (
    GetCountriesQuery,
    GetCountriesQueryHandler,
)
from globkurier_mcp.config.settings import Settings
from globkurier_mcp.infrastructure.cache import CachedCountryRepository
from globkurier_mcp.infrastructure.http.countries_client import GlobKurierCountriesClient
from globkurier_mcp.infrastructure.logging import setup_logging


async def test_countries():
    """Test countries resource with caching."""
    # Setup
    settings = Settings(
        globkurier_api_base_url="https://api.globkurier.pl",
        log_level="DEBUG",
        log_requests=True,
        cache_countries_ttl_seconds=10,  # 10 seconds for testing
    )
    setup_logging(settings)

    # Create infrastructure
    http_client = GlobKurierCountriesClient(settings=settings)
    cached_repo = CachedCountryRepository(
        repository=http_client,
        ttl_seconds=settings.cache_countries_ttl_seconds,
    )

    # Create handler
    handler = GetCountriesQueryHandler(country_repository=cached_repo)

    try:
        print("\n=== TEST 1: First request (should fetch from API) ===")
        result1 = await handler.handle(GetCountriesQuery())
        print(f"\nCountries count: {result1.total_count}")
        print(f"Cached: {result1.cached}")
        print(f"\nFirst 3 countries:")
        for country in result1.countries[:3]:
            print(f"  - {country.name} ({country.iso_code}) - EU: {country.is_ue_member}")

        print("\n=== TEST 2: Second request (should use cache) ===")
        result2 = await handler.handle(GetCountriesQuery())
        print(f"\nCountries count: {result2.total_count}")
        print(f"Cached: {result2.cached}")

        print("\n=== TEST 3: Wait for cache expiry ===")
        print("Waiting 11 seconds for cache to expire...")
        await asyncio.sleep(11)

        result3 = await handler.handle(GetCountriesQuery())
        print(f"\nCountries count: {result3.total_count}")
        print(f"Cached: {result3.cached}")
        print("(Should fetch fresh data after cache expiry)")

        print("\n=== JSON Output Sample ===")
        json_output = result1.model_dump_json(indent=2)
        print(json_output[:500] + "...")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await http_client.close()


if __name__ == "__main__":
    asyncio.run(test_countries())
