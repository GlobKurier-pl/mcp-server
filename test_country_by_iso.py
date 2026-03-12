"""Test script for country by ISO resource."""

import asyncio

from globkurier_mcp.application.queries.get_countries import (
    GetCountryByIsoQuery,
    GetCountryByIsoQueryHandler,
)
from globkurier_mcp.config.settings import Settings
from globkurier_mcp.infrastructure.cache import CachedCountryRepository
from globkurier_mcp.infrastructure.http.countries_client import GlobKurierCountriesClient
from globkurier_mcp.infrastructure.logging import setup_logging


async def test_country_by_iso():
    """Test country lookup by ISO code."""
    # Setup
    settings = Settings(
        globkurier_api_base_url="https://api.globkurier.pl",
        log_level="INFO",
        log_requests=False,
        cache_countries_ttl_seconds=3600,  # 1 hour
    )
    setup_logging(settings)

    # Create infrastructure
    http_client = GlobKurierCountriesClient(settings=settings)
    cached_repo = CachedCountryRepository(
        repository=http_client,
        ttl_seconds=settings.cache_countries_ttl_seconds,
    )

    # Create handler
    handler = GetCountryByIsoQueryHandler(country_repository=cached_repo)

    try:
        test_cases = [
            ("PL", "Poland"),
            ("pl", "Poland (lowercase test)"),
            ("US", "United States"),
            ("GB1", "England (regional code)"),
            ("ES2", "Spain islands"),
            ("XX", "Non-existent country (should fail)"),
        ]

        for iso_code, description in test_cases:
            print(f"\n{'='*60}")
            print(f"Testing: {description} (ISO: {iso_code})")
            print('='*60)

            try:
                result = await handler.handle(GetCountryByIsoQuery(iso_code=iso_code))

                print(f"SUCCESS!")
                print(f"  Name: {result.name}")
                print(f"  ISO Code: {result.iso_code}")
                print(f"  EU Member: {result.is_ue_member}")
                print(f"  Road Transport: {result.is_road_transport_available}")
                print(f"  Phone Prefix: {result.phone_prefix}")
                print(f"  Post Code Format: {result.post_code_format}")

            except ValueError as e:
                print(f"EXPECTED ERROR: {e}")
            except Exception as e:
                print(f"UNEXPECTED ERROR: {e}")
                import traceback
                traceback.print_exc()

    finally:
        await http_client.close()


if __name__ == "__main__":
    asyncio.run(test_country_by_iso())
