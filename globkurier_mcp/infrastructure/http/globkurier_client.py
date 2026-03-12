import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from globkurier_mcp.config.settings import Settings
from globkurier_mcp.core.shipping.models import Address, ShipmentId, ShipmentStatus, TrackingEvent
from globkurier_mcp.core.shipping.ports import (
    ShipmentNotFoundError,
    ShipmentTrackingPort,
    TrackingServiceError,
)

logger = logging.getLogger(__name__)


class GlobKurierHttpClient(ShipmentTrackingPort):
    """HTTP adapter implementing ShipmentTrackingPort for GlobKurier API.

    This is the concrete implementation of the port, adapting the external
    HTTP API to our domain interface.
    """

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

    async def get_shipment_status(
        self,
        shipment_id: ShipmentId,
        language: str,
    ) -> ShipmentStatus:
        """Fetch shipment status from GlobKurier API.

        Args:
            shipment_id: The shipment to track
            language: Language code (pl/en)

        Returns:
            ShipmentStatus: Parsed domain model

        Raises:
            ShipmentNotFoundError: When shipment doesn't exist
            TrackingServiceError: When API call fails
        """
        client = await self._get_client()

        # Log request if enabled
        if self._settings.log_requests:
            logger.info(
                f"Requesting shipment status: shipment_id={shipment_id}, language={language}"
            )

        try:
            response = await client.get(
                "/v1/order/tracking",
                params={"orderNumber": str(shipment_id)},
                headers={"Accept-Language": language},
            )

            # Log response
            if self._settings.log_requests:
                logger.info(
                    f"Received response: status={response.status_code}, "
                    f"shipment_id={shipment_id}"
                )
                logger.debug(
                    f"Response body for {shipment_id}: {response.text[:500]}"
                )

            if response.status_code == 404:
                logger.warning(f"Shipment not found: {shipment_id}")
                raise ShipmentNotFoundError(shipment_id)

            response.raise_for_status()
            data = response.json()

            logger.info(f"Successfully parsed shipment status for {shipment_id}")
            return self._map_to_domain(data, shipment_id, language)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Shipment not found (404): {shipment_id}")
                raise ShipmentNotFoundError(shipment_id)
            logger.error(
                f"HTTP error for {shipment_id}: status={e.response.status_code}, "
                f"error={str(e)}"
            )
            raise TrackingServiceError(
                f"HTTP error occurred: {e.response.status_code}",
                original_error=e,
            )
        except httpx.RequestError as e:
            logger.error(f"Request failed for {shipment_id}: {str(e)}")
            raise TrackingServiceError(
                f"Request failed: {str(e)}",
                original_error=e,
            )
        except Exception as e:
            logger.exception(f"Unexpected error for {shipment_id}: {str(e)}")
            raise TrackingServiceError(
                f"Unexpected error: {str(e)}",
                original_error=e,
            )

    def _map_to_domain(
        self,
        api_response: dict[str, Any],
        shipment_id: ShipmentId,
        language: str,
    ) -> ShipmentStatus:
        """Map API response to domain model.

        This method adapts the external API structure to our domain model,
        isolating the domain from external API changes.

        Expected API structure:
        {
            "latestStatus": {"type": "...", "name": "...", ...},
            "statuses": [{"type": "...", "name": "...", "date": "...", ...}]
        }
        """
        # Extract current status from latestStatus
        latest_status = api_response.get("latestStatus", {})
        current_status = latest_status.get("type", "UNKNOWN")
        current_description = latest_status.get("name", "")

        # Parse tracking events from statuses array
        events_data = api_response.get("statuses", [])
        events = [self._parse_tracking_event(event_data) for event_data in events_data]

        # Parse addresses
        sender_address = self._parse_address(api_response.get("senderAddress"))
        receiver_address = self._parse_address(api_response.get("receiverAddress"))

        logger.debug(
            f"Mapped API response: status={current_status}, "
            f"events_count={len(events)}, "
            f"has_sender={sender_address is not None}, "
            f"has_receiver={receiver_address is not None}"
        )

        return ShipmentStatus(
            shipment_id=shipment_id,
            current_status=current_status,
            current_description=current_description,
            events=events,
            language=language,  # type: ignore
            retrieved_at=datetime.now(UTC),
            sender_address=sender_address,
            receiver_address=receiver_address,
        )

    def _parse_tracking_event(self, event_data: dict[str, Any]) -> TrackingEvent:
        """Parse a single tracking event from API data.

        Expected event structure:
        {
            "type": "REGISTERED_IN_SYSTEM",
            "date": "2025-04-16 21:14:07",
            "location": null,
            "name": "Zarejestrowano w systemie GlobKurier.pl",
            "description": null,
            "number": "640156498521020033598657"
        }
        """
        # Parse timestamp from "date" field
        timestamp_str = event_data.get("date", "")
        timestamp = self._parse_timestamp(timestamp_str)

        # Status type (e.g., "REGISTERED_IN_SYSTEM")
        status_type = event_data.get("type", "UNKNOWN")

        # Description is the "name" field, optionally with additional "description"
        main_name = event_data.get("name", "")
        additional_desc = event_data.get("description")

        # Combine name and description if both exist
        if main_name and additional_desc:
            description = f"{main_name} - {additional_desc}"
        else:
            description = main_name or additional_desc or "No description"

        # Tracking number from carrier
        tracking_number = event_data.get("number")

        return TrackingEvent(
            timestamp=timestamp,
            status=status_type,
            description=description,
            location=event_data.get("location"),
            tracking_number=tracking_number,
        )

    def _parse_address(self, address_data: dict[str, Any] | None) -> Address | None:
        """Parse address from API data.

        Expected address structure:
        {
            "city": "Katowice",
            "street": "",
            "houseNumber": "",
            "apartmentNumber": "",
            "postCode": "40-074",
            "countryId": 1
        }
        """
        if not address_data:
            return None

        try:
            # Required fields
            city = address_data.get("city", "").strip()
            post_code = address_data.get("postCode", "").strip()
            country_id = address_data.get("countryId", 0)

            if not city or not post_code:
                logger.debug("Skipping address with missing required fields")
                return None

            # Optional fields (empty strings should be None)
            street = address_data.get("street", "").strip() or None
            house_number = address_data.get("houseNumber", "").strip() or None
            apartment_number = address_data.get("apartmentNumber", "").strip() or None

            return Address(
                city=city,
                post_code=post_code,
                country_id=country_id,
                street=street,
                house_number=house_number,
                apartment_number=apartment_number,
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse address: {e}")
            return None

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from various formats."""
        if not timestamp_str:
            return datetime.now(UTC)

        # Try common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # Fallback
        return datetime.now(UTC)

    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
