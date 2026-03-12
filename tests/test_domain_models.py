"""Example tests for domain models - demonstrating hexagonal architecture testing."""

from datetime import datetime, timezone

import pytest

from globkurier_mcp.core.shipping.models import ShipmentId, ShipmentStatus, TrackingEvent


def test_shipment_id_value_object():
    """Test ShipmentId value object validation."""
    # Valid shipment ID
    shipment_id = ShipmentId(value="GK160825421616")
    assert str(shipment_id) == "GK160825421616"

    # Empty shipment ID should raise error
    with pytest.raises(ValueError, match="ShipmentId cannot be empty"):
        ShipmentId(value="")


def test_tracking_event_immutability():
    """Test TrackingEvent is immutable (frozen dataclass)."""
    event = TrackingEvent(
        timestamp=datetime(2024, 1, 15, 10, 30),
        status="delivered",
        description="Package delivered",
        location="Warsaw",
    )

    # Should not be able to modify frozen dataclass
    with pytest.raises(Exception):
        event.status = "pending"  # type: ignore


def test_shipment_status_is_delivered():
    """Test domain logic: is_delivered() method."""
    shipment_id = ShipmentId("GK123")

    # Delivered shipment
    delivered = ShipmentStatus(
        shipment_id=shipment_id,
        current_status="delivered",
        current_description="Delivered",
        events=[],
        language="pl",
        retrieved_at=datetime.now(timezone.utc),
    )
    assert delivered.is_delivered() is True

    # Pending shipment
    pending = ShipmentStatus(
        shipment_id=shipment_id,
        current_status="in_transit",
        current_description="In transit",
        events=[],
        language="pl",
        retrieved_at=datetime.now(timezone.utc),
    )
    assert pending.is_delivered() is False


def test_shipment_status_get_latest_event():
    """Test getting the latest tracking event."""
    events = [
        TrackingEvent(
            timestamp=datetime(2024, 1, 15, 10, 0),
            status="picked_up",
            description="Picked up",
        ),
        TrackingEvent(
            timestamp=datetime(2024, 1, 15, 14, 0),
            status="in_transit",
            description="In transit",
        ),
        TrackingEvent(
            timestamp=datetime(2024, 1, 15, 12, 0),
            status="at_depot",
            description="At depot",
        ),
    ]

    shipment = ShipmentStatus(
        shipment_id=ShipmentId("GK123"),
        current_status="in_transit",
        current_description="In transit",
        events=events,
        language="pl",
        retrieved_at=datetime.now(timezone.utc),
    )

    latest = shipment.get_latest_event()
    assert latest is not None
    assert latest.status == "in_transit"
    assert latest.timestamp == datetime(2024, 1, 15, 14, 0)
