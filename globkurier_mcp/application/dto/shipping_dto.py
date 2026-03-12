from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AddressDto(BaseModel):
    """DTO for postal address."""

    city: str
    post_code: str
    country_id: int
    street: str | None = None
    house_number: str | None = None
    apartment_number: str | None = None


class TrackingEventDto(BaseModel):
    """DTO for a single tracking event."""

    timestamp: datetime
    status: str
    description: str
    location: str | None = None
    tracking_number: str | None = None


class ShipmentStatusDto(BaseModel):
    """DTO for complete shipment status.

    This is the contract between Application and Infrastructure layers.
    It's designed for serialization and API responses.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "shipment_id": "GK160825421616",
                "current_status": "delivered",
                "current_description": "Przesyłka została doręczona",
                "events": [
                    {
                        "timestamp": "2024-01-15T10:30:00",
                        "status": "delivered",
                        "description": "Doręczono odbiorcę",
                        "location": "Warsaw",
                    }
                ],
                "language": "pl",
                "retrieved_at": "2024-01-15T12:00:00",
                "is_delivered": True,
                "total_events": 5,
            }
        }
    )

    shipment_id: str = Field(..., description="Unique shipment identifier")
    current_status: str = Field(..., description="Current shipment status")
    current_description: str = Field(..., description="Human-readable status description")
    events: list[TrackingEventDto] = Field(default_factory=list, description="Tracking history")
    language: str = Field(..., description="Language code (pl/en)")
    retrieved_at: datetime = Field(..., description="When this data was retrieved")
    is_delivered: bool = Field(..., description="Whether shipment has been delivered")
    total_events: int = Field(..., description="Total number of tracking events")
    sender_address: AddressDto | None = Field(None, description="Sender postal address")
    receiver_address: AddressDto | None = Field(None, description="Receiver postal address")
