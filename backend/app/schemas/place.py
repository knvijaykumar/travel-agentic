from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Place(BaseModel):
    """Pydantic v2 schema representing a normalized physical place / attraction."""

    place_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the place",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Name of the place",
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Category classification of the place",
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90 to 90)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180 to 180)",
    )
    address: Optional[str] = Field(
        default=None,
        description="Full formatted street or location address",
    )
    city: Optional[str] = Field(
        default=None,
        description="City or locality name",
    )
    country: Optional[str] = Field(
        default=None,
        description="Country name",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL to an image of the place",
    )
    image_attribution: Optional[str] = Field(
        default=None,
        description="Attribution or credit information for the image",
    )
    source_provider: str = Field(
        ...,
        min_length=1,
        description="Source provider of place data (e.g., Geoapify, OpenStreetMap)",
    )

    @field_validator("name", "source_provider", "place_id")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        """Ensure critical string fields are not blank or whitespace-only."""
        if not value or not value.strip():
            raise ValueError("Field cannot be empty or whitespace-only.")
        return value.strip()

