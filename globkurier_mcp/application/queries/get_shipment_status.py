import logging
from dataclasses import dataclass

from globkurier_mcp.application.dto.shipping_dto import (
    AddressDto,
    ShipmentStatusDto,
    TrackingEventDto,
)
from globkurier_mcp.core.shipping.models import Address, ShipmentId, ShipmentStatus
from globkurier_mcp.core.shipping.ports import ShipmentTrackingPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetShipmentStatusQuery:
    """Query to retrieve shipment status.

    This is the command object in CQRS pattern for read operations.
    """

    order_number: str
    language: str = "pl"


class GetShipmentStatusQueryHandler:
    """Handler for GetShipmentStatusQuery.

    This handler executes the query by:
    1. Validating input
    2. Calling domain services via ports
    3. Mapping domain models to DTOs
    """

    def __init__(self, tracking_port: ShipmentTrackingPort) -> None:
        self._tracking_port = tracking_port

    async def handle(self, query: GetShipmentStatusQuery) -> ShipmentStatusDto:
        """Execute the query and return DTO.

        Args:
            query: The query to execute

        Returns:
            ShipmentStatusDto: The result as a data transfer object
        """
        logger.info(
            f"Handling GetShipmentStatusQuery: order_number={query.order_number}, "
            f"language={query.language}"
        )

        # Create domain value object
        shipment_id = ShipmentId(value=query.order_number)

        # Use port to get domain model
        shipment_status = await self._tracking_port.get_shipment_status(
            shipment_id=shipment_id,
            language=query.language,
        )

        # Map domain model to DTO
        dto = self._map_to_dto(shipment_status)

        logger.info(
            f"Successfully handled query for {query.order_number}: "
            f"status={dto.current_status}, events={dto.total_events}"
        )

        return dto

    def _map_to_dto(self, domain_model: ShipmentStatus) -> ShipmentStatusDto:
        """Map domain model to DTO.

        This keeps the domain layer independent of serialization concerns.
        """
        return ShipmentStatusDto(
            shipment_id=str(domain_model.shipment_id),
            current_status=domain_model.current_status,
            current_description=domain_model.current_description,
            events=[
                TrackingEventDto(
                    timestamp=event.timestamp,
                    status=event.status,
                    description=event.description,
                    location=event.location,
                    tracking_number=event.tracking_number,
                )
                for event in domain_model.events
            ],
            language=domain_model.language,
            retrieved_at=domain_model.retrieved_at,
            is_delivered=domain_model.is_delivered(),
            total_events=len(domain_model.events),
            sender_address=self._map_address_to_dto(domain_model.sender_address),
            receiver_address=self._map_address_to_dto(domain_model.receiver_address),
        )

    def _map_address_to_dto(self, address: Address | None) -> AddressDto | None:
        """Map address domain model to DTO."""
        if not address:
            return None
        return AddressDto(
            city=address.city,
            post_code=address.post_code,
            country_id=address.country_id,
            street=address.street,
            house_number=address.house_number,
            apartment_number=address.apartment_number,
        )
