"""DTOs for countries bounded context."""

from pydantic import BaseModel, Field


class CountryDto(BaseModel):
    """DTO for a single country."""

    id: int = Field(..., description="Unique country identifier")
    name: str = Field(..., description="Country name")
    iso_code: str = Field(..., description="ISO 3166-1 alpha-2 code")
    is_ue_member: bool = Field(..., description="Whether country is EU member")
    is_road_transport_available: bool = Field(..., description="Road transport availability")
    has_states: bool = Field(..., description="Whether country has states/provinces")
    has_post_codes: bool = Field(..., description="Whether country uses postal codes")
    post_code_format: str | None = Field(None, description="Postal code format pattern")
    phone_prefix: str = Field(..., description="International phone prefix")
    post_code_samples: str | None = Field(None, description="Example postal codes")


class CountriesListDto(BaseModel):
    """DTO for list of countries."""

    countries: list[CountryDto] = Field(..., description="List of available countries")
    total_count: int = Field(..., description="Total number of countries")
    cached: bool = Field(..., description="Whether data was served from cache")
