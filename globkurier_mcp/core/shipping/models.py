from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class ShipmentId:
    """Value Object representing a shipment identifier."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("ShipmentId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TrackingEvent:
    """Value Object representing a single tracking event in shipment history."""

    timestamp: datetime
    status: str
    description: str
    location: str | None = None
    tracking_number: str | None = None  # Carrier tracking number

    def __post_init__(self) -> None:
        if not self.status:
            raise ValueError("Status cannot be empty")
        if not self.description:
            raise ValueError("Description cannot be empty")


@dataclass(frozen=True)
class Address:
    """Value Object representing a postal address."""

    city: str
    post_code: str
    country_id: int
    street: str | None = None
    house_number: str | None = None
    apartment_number: str | None = None

    def __post_init__(self) -> None:
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.post_code:
            raise ValueError("Post code cannot be empty")

    def __str__(self) -> str:
        """Format address as readable string."""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.house_number:
            parts.append(self.house_number)
        if self.apartment_number:
            parts.append(f"/{self.apartment_number}")
        parts.append(f"{self.post_code} {self.city}")
        return " ".join(parts)


@dataclass
class ShipmentStatus:
    """Aggregate root representing complete shipment tracking information."""

    shipment_id: ShipmentId
    current_status: str
    current_description: str
    events: list[TrackingEvent]
    language: Literal["pl", "en"]
    retrieved_at: datetime
    sender_address: Address | None = None
    receiver_address: Address | None = None

    def __post_init__(self) -> None:
        if not self.current_status:
            raise ValueError("Current status cannot be empty")
        if not isinstance(self.events, list):
            raise ValueError("Events must be a list")

    def has_events(self) -> bool:
        """Check if shipment has any tracking events."""
        return len(self.events) > 0

    def get_latest_event(self) -> TrackingEvent | None:
        """Get the most recent tracking event."""
        if not self.events:
            return None
        return max(self.events, key=lambda e: e.timestamp)

    def is_delivered(self) -> bool:
        """Check if shipment has been delivered."""
        delivered_statuses = {"delivered", "dostarczono", "doręczono"}
        return self.current_status.lower() in delivered_statuses
