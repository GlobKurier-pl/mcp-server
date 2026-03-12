"""Domain models for countries bounded context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    """Value Object representing a country with shipping information."""

    id: int
    name: str
    iso_code: str
    is_ue_member: bool
    is_road_transport_available: bool
    has_states: bool
    has_post_codes: bool
    post_code_format: str | None
    phone_prefix: str
    post_code_samples: str | None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Country name cannot be empty")
        if not self.iso_code:
            raise ValueError("ISO code cannot be empty")
        # Note: Some countries may have non-standard ISO codes from API
        # We log warning but don't fail

    def __str__(self) -> str:
        """String representation showing name and ISO code."""
        return f"{self.name} ({self.iso_code})"
