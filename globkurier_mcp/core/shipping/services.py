from globkurier_mcp.core.shipping.models import ShipmentId, ShipmentStatus
from globkurier_mcp.core.shipping.ports import ShipmentTrackingPort


class ShipmentTrackingService:
    """Domain service for shipment tracking operations.

    This service orchestrates domain logic that doesn't naturally fit
    within a single entity or value object.
    """

    def __init__(self, tracking_port: ShipmentTrackingPort) -> None:
        self._tracking_port = tracking_port

    async def track_shipment(
        self,
        shipment_id: ShipmentId,
        language: str = "pl",
    ) -> ShipmentStatus:
        """Track a shipment using the configured tracking port.

        Args:
            shipment_id: The shipment to track
            language: Preferred language for descriptions

        Returns:
            ShipmentStatus: Current tracking information
        """
        return await self._tracking_port.get_shipment_status(
            shipment_id=shipment_id,
            language=language,
        )
