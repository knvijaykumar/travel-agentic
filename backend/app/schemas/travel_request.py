from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TravelRequest(BaseModel):
    """Pydantic v2 schema for validating incoming travel planning requests."""

    destination: str = Field(
        ...,
        min_length=1,
        description="Target destination (required, non-empty)",
    )
    duration_days: int = Field(
        ...,
        gt=0,
        description="Trip duration in days (must be greater than 0)",
    )
    travellers: int = Field(
        ...,
        gt=0,
        description="Number of travellers (must be greater than 0)",
    )
    budget: float = Field(
        ...,
        gt=0,
        description="Total travel budget (must be greater than 0)",
    )
    currency: str = Field(
        default="INR",
        description="Currency code (default 'INR')",
    )
    interests: List[str] = Field(
        default_factory=list,
        description="List of traveller interests or activity tags (safe default empty list)",
    )
    departure_city: Optional[str] = Field(
        default=None,
        description="Optional departure city",
    )
    travel_date: Optional[str] = Field(
        default=None,
        description="Optional travel start date",
    )

    @field_validator("destination")
    @classmethod
    def validate_destination_non_empty(cls, value: str) -> str:
        """Ensure destination is not blank or whitespace-only."""
        if not value or not value.strip():
            raise ValueError("Destination cannot be empty or whitespace-only.")
        return value.strip()

