"""Example tests for query handlers - demonstrating port/adapter mocking."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from globkurier_mcp.application.queries.get_shipment_status import (
    GetShipmentStatusQuery,
    GetShipmentStatusQueryHandler,
)
from globkurier_mcp.core.shipping.models import ShipmentId, ShipmentStatus, TrackingEvent


@pytest.fixture
def mock_tracking_port():
    """Mock ShipmentTrackingPort - this is the power of hexagonal architecture!"""
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_shipment_status_query_handler(mock_tracking_port):
    """Test query handler with mocked port."""
    # Arrange - setup mock data
    expected_shipment = ShipmentStatus(
        shipment_id=ShipmentId("GK123"),
        current_status="delivered",
        current_description="Package delivered",
        events=[
            TrackingEvent(
                timestamp=datetime(2024, 1, 15, 10, 0),
                status="delivered",
                description="Delivered to recipient",
                location="Warsaw",
            )
        ],
        language="pl",
        retrieved_at=datetime(2024, 1, 15, 12, 0),
    )
    mock_tracking_port.get_shipment_status.return_value = expected_shipment

    # Create handler with mocked port
    handler = GetShipmentStatusQueryHandler(tracking_port=mock_tracking_port)

    # Act - execute query
    query = GetShipmentStatusQuery(order_number="GK123", language="pl")
    result = await handler.handle(query)

    # Assert - verify DTO mapping
    assert result.shipment_id == "GK123"
    assert result.current_status == "delivered"
    assert result.is_delivered is True
    assert result.total_events == 1
    assert len(result.events) == 1
    assert result.events[0].status == "delivered"

    # Verify port was called correctly
    mock_tracking_port.get_shipment_status.assert_called_once()
    call_args = mock_tracking_port.get_shipment_status.call_args
    assert str(call_args[1]["shipment_id"]) == "GK123"
    assert call_args[1]["language"] == "pl"
