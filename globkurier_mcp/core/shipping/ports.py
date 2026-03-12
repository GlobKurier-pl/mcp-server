from abc import ABC, abstractmethod

from globkurier_mcp.core.shipping.models import ShipmentId, ShipmentStatus


class ShipmentTrackingPort(ABC):
    """Port (interface) for shipment tracking operations.

    This is the contract that infrastructure adapters must implement.
    It defines the domain's requirements without coupling to specific implementations.
    """

    @abstractmethod
    async def get_shipment_status(
        self,
        shipment_id: ShipmentId,
        language: str,
    ) -> ShipmentStatus:
        """Retrieve shipment status from external tracking system.

        Args:
            shipment_id: The unique identifier of the shipment
            language: Language code for status descriptions (pl/en)

        Returns:
            ShipmentStatus: Complete tracking information

        Raises:
            ShipmentNotFoundError: When shipment doesn't exist
            TrackingServiceError: When external service fails
        """
        pass


class ShipmentNotFoundError(Exception):
    """Raised when shipment cannot be found in tracking system."""

    def __init__(self, shipment_id: ShipmentId) -> None:
        self.shipment_id = shipment_id
        super().__init__(f"Shipment not found: {shipment_id}")


class TrackingServiceError(Exception):
    """Raised when tracking service encounters an error."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error
        super().__init__(message)
