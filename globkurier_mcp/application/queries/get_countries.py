"""Query for retrieving countries list."""

import logging
from dataclasses import dataclass

from globkurier_mcp.application.dto.countries_dto import CountriesListDto, CountryDto
from globkurier_mcp.core.countries.models import Country
from globkurier_mcp.core.countries.ports import CountryRepositoryPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetCountriesQuery:
    """Query to retrieve all available countries.

    This is a simple query with no parameters - it returns all countries.
    """

    pass


@dataclass(frozen=True)
class GetCountryByIsoQuery:
    """Query to retrieve a specific country by ISO code.

    Args:
        iso_code: ISO 3166-1 alpha-2 or custom code (e.g., 'PL', 'GB1')
    """

    iso_code: str

    def __post_init__(self) -> None:
        if not self.iso_code or not self.iso_code.strip():
            raise ValueError("ISO code cannot be empty")


class GetCountriesQueryHandler:
    """Handler for GetCountriesQuery."""

    def __init__(self, country_repository: CountryRepositoryPort) -> None:
        self._country_repository = country_repository

    async def handle(self, query: GetCountriesQuery) -> CountriesListDto:
        """Execute the query and return DTO.

        Args:
            query: The query to execute

        Returns:
            CountriesListDto: The result as a data transfer object
        """
        logger.info("Handling GetCountriesQuery")

        # Fetch countries from repository (may be cached)
        countries = await self._country_repository.get_all_countries()

        # Map to DTO
        dto = self._map_to_dto(countries)

        logger.info(
            f"Successfully handled GetCountriesQuery: "
            f"total={dto.total_count}, cached={dto.cached}"
        )

        return dto

    def _map_to_dto(self, countries: list[Country]) -> CountriesListDto:
        """Map domain models to DTO."""
        # Check if data is cached (simple heuristic - if we have cached repository)
        from globkurier_mcp.infrastructure.cache import CachedCountryRepository

        is_cached = isinstance(self._country_repository, CachedCountryRepository)

        return CountriesListDto(
            countries=[
                CountryDto(
                    id=country.id,
                    name=country.name,
                    iso_code=country.iso_code,
                    is_ue_member=country.is_ue_member,
                    is_road_transport_available=country.is_road_transport_available,
                    has_states=country.has_states,
                    has_post_codes=country.has_post_codes,
                    post_code_format=country.post_code_format,
                    phone_prefix=country.phone_prefix,
                    post_code_samples=country.post_code_samples,
                )
                for country in countries
            ],
            total_count=len(countries),
            cached=is_cached,
        )


class GetCountryByIsoQueryHandler:
    """Handler for GetCountryByIsoQuery."""

    def __init__(self, country_repository: CountryRepositoryPort) -> None:
        self._country_repository = country_repository

    async def handle(self, query: GetCountryByIsoQuery) -> CountryDto:
        """Execute the query and return DTO for a specific country.

        Args:
            query: The query with ISO code

        Returns:
            CountryDto: The country matching the ISO code

        Raises:
            ValueError: If country with given ISO code is not found
        """
        logger.info(f"Handling GetCountryByIsoQuery: iso_code={query.iso_code}")

        # Fetch all countries from repository (cached)
        countries = await self._country_repository.get_all_countries()

        # Find country by ISO code (case-insensitive)
        iso_upper = query.iso_code.upper()
        matching_country = next(
            (c for c in countries if c.iso_code.upper() == iso_upper),
            None,
        )

        if not matching_country:
            logger.warning(f"Country not found for ISO code: {query.iso_code}")
            raise ValueError(f"Country with ISO code '{query.iso_code}' not found")

        logger.info(
            f"Successfully found country: {matching_country.name} ({matching_country.iso_code})"
        )

        # Map to DTO
        return CountryDto(
            id=matching_country.id,
            name=matching_country.name,
            iso_code=matching_country.iso_code,
            is_ue_member=matching_country.is_ue_member,
            is_road_transport_available=matching_country.is_road_transport_available,
            has_states=matching_country.has_states,
            has_post_codes=matching_country.has_post_codes,
            post_code_format=matching_country.post_code_format,
            phone_prefix=matching_country.phone_prefix,
            post_code_samples=matching_country.post_code_samples,
        )
