"""Cached country repository with TTL."""

import logging
from datetime import UTC, datetime, timedelta

from globkurier_mcp.core.countries.models import Country
from globkurier_mcp.core.countries.ports import CountryRepositoryPort

logger = logging.getLogger(__name__)


class CachedCountryRepository(CountryRepositoryPort):
    """Decorator that adds caching with TTL to country repository.

    This implements the Decorator pattern - it wraps another repository
    and adds caching behavior without changing the interface.
    """

    def __init__(
        self,
        repository: CountryRepositoryPort,
        ttl_seconds: int,
    ) -> None:
        """Initialize cached repository.

        Args:
            repository: The underlying repository to cache
            ttl_seconds: Time-to-live for cache in seconds
        """
        self._repository = repository
        self._ttl_seconds = ttl_seconds
        self._cache: list[Country] | None = None
        self._cache_timestamp: datetime | None = None

        logger.info(
            f"Initialized CachedCountryRepository with TTL={ttl_seconds}s "
            f"({ttl_seconds / 86400:.1f} days)"
        )

    async def get_all_countries(self) -> list[Country]:
        """Get all countries with caching.

        Returns cached data if available and not expired,
        otherwise fetches fresh data from underlying repository.
        """
        now = datetime.now(UTC)

        # Check if cache exists and is still valid
        if self._cache is not None and self._cache_timestamp is not None:
            cache_age = (now - self._cache_timestamp).total_seconds()
            if cache_age < self._ttl_seconds:
                logger.info(
                    f"Returning cached countries (age: {cache_age:.1f}s, "
                    f"expires in: {self._ttl_seconds - cache_age:.1f}s)"
                )
                return self._cache

            logger.info(
                f"Cache expired (age: {cache_age:.1f}s > TTL: {self._ttl_seconds}s), "
                "fetching fresh data"
            )

        # Cache miss or expired - fetch fresh data
        logger.info("Cache miss - fetching countries from API")
        countries = await self._repository.get_all_countries()

        # Update cache
        self._cache = countries
        self._cache_timestamp = now

        logger.info(
            f"Cached {len(countries)} countries, "
            f"expires at {(now + timedelta(seconds=self._ttl_seconds)).isoformat()}"
        )

        return countries

    def clear_cache(self) -> None:
        """Manually clear the cache."""
        logger.info("Manually clearing countries cache")
        self._cache = None
        self._cache_timestamp = None
