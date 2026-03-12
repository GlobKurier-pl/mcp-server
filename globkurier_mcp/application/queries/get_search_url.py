"""Query for generating GlobKurier search page URL.

This module implements CQRS pattern for building a search URL
that allows users to complete a purchase on the GlobKurier portal.
"""

import logging
from dataclasses import dataclass
from urllib.parse import urlencode

from globkurier_mcp.application.dto.product_dto import SearchUrlDto

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetSearchUrlQuery:
    """Query to generate a GlobKurier search page URL.

    Attributes:
        width: Package width in cm
        height: Package height in cm
        length: Package length in cm
        weight: Package weight in kg
        quantity: Number of packages
        sender_country_id: Sender country ID
        receiver_country_id: Receiver country ID
        product_id: Optional product ID to pre-select on the search page
    """

    width: int
    height: int
    length: int
    weight: int
    quantity: int
    sender_country_id: int
    receiver_country_id: int
    product_id: int


class GetSearchUrlQueryHandler:
    """Handler for GetSearchUrlQuery.

    Builds a URL to the GlobKurier search page with pre-filled parameters.
    No external API calls are made - this is a pure URL construction operation.
    """

    def __init__(self, portal_base_url: str) -> None:
        """Initialize handler with portal base URL.

        Args:
            portal_base_url: Base URL of the GlobKurier portal (e.g. https://www.globkurier.pl)
        """
        self._portal_base_url = portal_base_url

    async def handle(self, query: GetSearchUrlQuery) -> SearchUrlDto:
        """Handle the query by building the search URL.

        Args:
            query: The query with shipment parameters

        Returns:
            SearchUrlDto containing the full search URL
        """
        logger.debug(
            f"Handling GetSearchUrlQuery: "
            f"sender_country={query.sender_country_id}, "
            f"receiver_country={query.receiver_country_id}, "
            f"product_id={query.product_id}"
        )

        params: dict[str, str | int | bool] = {
            "width": query.width,
            "height": query.height,
            "length": query.length,
            "weight": query.weight,
            "quantity": query.quantity,
            "senderCountryId": query.sender_country_id,
            "receiverCountryId": query.receiver_country_id,
            "flatList": "true",
        }

        params["productId"] = query.product_id

        url = f"{self._portal_base_url.rstrip('/')}/search?{urlencode(params)}"

        logger.info(f"Generated search URL for product_id={query.product_id}")

        return SearchUrlDto(url=url)
