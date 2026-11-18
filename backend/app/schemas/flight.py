from datetime import date
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


VALID_CABIN_CLASSES = {"economy", "premium_economy", "business", "first"}


class FlightSearchRequest(BaseModel):
    """Pydantic v2 schema for flight search request validation."""

    origin: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="3-letter IATA airport or metro code for departure (e.g., 'DEL', 'BOM')",
        examples=["DEL"],
    )
    destination: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="3-letter IATA airport or metro code for arrival (e.g., 'GOI', 'BLR')",
        examples=["GOI"],
    )
    departure_date: str = Field(
        ...,
        description="Departure date in YYYY-MM-DD format (e.g., '2026-12-01')",
        examples=["2026-12-01"],
    )
    adults: int = Field(
        default=1,
        ge=1,
        le=9,
        description="Number of adult passengers (age 12+, 1-9)",
    )
    cabin_class: str = Field(
        default="economy",
        description="Cabin class: 'economy', 'premium_economy', 'business', or 'first'",
    )

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata_code(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", clean):
            raise ValueError("Airport code must be a valid 3-letter IATA string (e.g. 'DEL').")
        return clean

    @field_validator("departure_date")
    @classmethod
    def validate_departure_date(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean):
            raise ValueError("Departure date must be formatted as YYYY-MM-DD.")
        try:
            date.fromisoformat(clean)
        except ValueError:
            raise ValueError("Departure date must be a valid calendar date formatted as YYYY-MM-DD.")
        return clean

    @field_validator("cabin_class")
    @classmethod
    def validate_cabin_class(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_CABIN_CLASSES:
            raise ValueError(f"Cabin class must be one of {sorted(VALID_CABIN_CLASSES)}.")
        return clean

    @model_validator(mode="after")
    def validate_origin_differs_from_destination(self) -> "FlightSearchRequest":
        if self.origin == self.destination:
            raise ValueError("Origin and destination airports cannot be the same.")
        return self

