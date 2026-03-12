"""HTTP adapter for countries endpoint."""

import logging
from typing import Any

import httpx

from globkurier_mcp.config.settings import Settings
from globkurier_mcp.core.countries.models import Country
from globkurier_mcp.core.countries.ports import CountryRepositoryError, CountryRepositoryPort

logger = logging.getLogger(__name__)


class GlobKurierCountriesClient(CountryRepositoryPort):
    """HTTP adapter for countries endpoint implementing CountryRepositoryPort."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client instance."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.globkurier_api_base_url.rstrip("/"),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self._settings.http_timeout,
            )
        return self._client

    async def get_all_countries(self) -> list[Country]:
        """Fetch all countries from GlobKurier API.

        Returns:
            List of Country domain models

        Raises:
            CountryRepositoryError: When API call fails
        """
        client = await self._get_client()

        if self._settings.log_requests:
            logger.info("Requesting countries list from API")

        try:
            response = await client.get("/v1/countries")

            if self._settings.log_requests:
                logger.info(f"Received countries response: status={response.status_code}")
                count = len(response.json() if response.status_code == 200 else [])
                logger.debug(f"Countries count: {count}")

            response.raise_for_status()
            data = response.json()

            countries = [self._map_to_domain(country_data) for country_data in data]

            logger.info(f"Successfully fetched {len(countries)} countries")
            return countries

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching countries: status={e.response.status_code}")
            raise CountryRepositoryError(
                f"HTTP error occurred: {e.response.status_code}",
                original_error=e,
            )
        except httpx.RequestError as e:
            logger.error(f"Request failed for countries: {str(e)}")
            raise CountryRepositoryError(
                f"Request failed: {str(e)}",
                original_error=e,
            )
        except Exception as e:
            logger.exception(f"Unexpected error fetching countries: {str(e)}")
            raise CountryRepositoryError(
                f"Unexpected error: {str(e)}",
                original_error=e,
            )

    def _map_to_domain(self, api_data: dict[str, Any]) -> Country:
        """Map API response to domain model.

        Expected API structure:
        {
            "id": 101,
            "name": "Afganistan",
            "isUEMember": false,
            "isRoadTransportAvailable": false,
            "isoCode": "AF",
            "hasStates": false,
            "hasPostCodes": true,
            "postCodeFormat": "????",
            "phonePrefix": "+93",
            "postCodeSamples": "1234"
        }
        """
        iso_code = api_data.get("isoCode", "")

        # Log warning for non-standard ISO codes
        if len(iso_code) != 2:
            logger.warning(
                f"Non-standard ISO code for country {api_data.get('name')}: "
                f"'{iso_code}' (length: {len(iso_code)})"
            )

        return Country(
            id=api_data["id"],
            name=api_data["name"],
            iso_code=iso_code or "XX",  # Use placeholder if empty
            is_ue_member=api_data.get("isUEMember", False),
            is_road_transport_available=api_data.get("isRoadTransportAvailable", False),
            has_states=api_data.get("hasStates", False),
            has_post_codes=api_data.get("hasPostCodes", True),
            post_code_format=api_data.get("postCodeFormat"),
            phone_prefix=api_data.get("phonePrefix", ""),
            post_code_samples=api_data.get("postCodeSamples"),
        )

    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
