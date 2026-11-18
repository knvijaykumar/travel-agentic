from datetime import date
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.schemas.place import Place
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import DurationMatrixResponse


class AirportCandidate(BaseModel):
    """Candidate airport resolved from a city name or query."""
    iata: str = Field(..., min_length=3, max_length=3, description="3-letter IATA code")
    name: str = Field(..., description="Full airport name")
    city: str = Field(..., description="City or metropolitan area served")
    country: Optional[str] = Field(default=None, description="Country name")


class AggregatedFlightSegment(BaseModel):
    """Individual flight segment within an itinerary."""
    carrier_code: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time_local: str
    arrival_time_local: str


class AggregatedFlightOption(BaseModel):
    """Normalized flight itinerary candidate."""
    flight_id: str
    direction: str = Field(..., description="'outbound' or 'return'")
    origin_iata: str = Field(..., min_length=3, max_length=3)
    destination_iata: str = Field(..., min_length=3, max_length=3)
    departure_date: str
    carrier: str
    duration_minutes: int
    price_amount: float
    currency: str = "INR"
    cabin_class: str = "economy"
    has_mixed_carriers: bool = False
    segments: List[AggregatedFlightSegment] = Field(default_factory=list)
    source_provider: str = "Ignav"
    is_indicative: bool = Field(default=False, description="True if price is an indicative estimate rather than a live booking offer")
    price_type: str = Field(default="live", description="'live' or 'indicative'")
    stops: int = Field(default=0, description="Number of intermediate stops")
    airline_logo_url: Optional[str] = Field(default=None, description="Optional verified airline logo URL")
    retrieved_at: Optional[str] = Field(default=None, description="Timestamp when fare was retrieved")
    booking_url: Optional[str] = Field(default=None, description="Optional genuine provider-supplied booking URL or deep link")

    @field_validator("booking_url", mode="before")
    @classmethod
    def validate_booking_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that any supplied booking URL uses a safe HTTP/HTTPS scheme."""
        if not v or not isinstance(v, str) or not v.strip():
            return None
        clean = v.strip()
        lower = clean.lower()
        if lower in ("http://", "https://") or "://" not in lower:
            raise ValueError("booking_url must be a valid URL")
        if not (lower.startswith("http://") or lower.startswith("https://")):
            raise ValueError("booking_url must use http or https scheme")
        return clean


class HotelRoomOffer(BaseModel):
    """Individual room type and rate offer from hotel provider."""
    offer_id: str
    room_name: str
    board_name: str = "Room Only"
    total_amount: float
    currency: str = "INR"
    cancellation_policy: Optional[str] = None
    taxes_and_fees: Optional[Dict[str, Any]] = None


class AggregatedHotelOption(BaseModel):
    """Normalized hotel candidate with metadata and room rate offers."""
    hotel_id: str
    name: str
    star_rating: Optional[int] = None
    user_rating: Optional[float] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    min_price_total: float
    min_price_per_night: float
    currency: str = "INR"
    offers: List[HotelRoomOffer] = Field(default_factory=list)
    is_sandbox: bool = True
    source_provider: str = "Nuitee/LiteAPI"


class ProviderExecutionStatus(BaseModel):
    """Execution status and diagnostics for an individual provider."""
    status: str = Field(..., description="'success', 'partial', 'failed', 'skipped', 'timed_out', or 'unavailable'")
    item_count: int = 0
    latency_seconds: float = 0.0
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class TripAggregationRequest(BaseModel):
    """Pydantic v2 schema for deterministic trip aggregation request validation."""

    destination: str = Field(
        ...,
        min_length=1,
        description="Target destination city or region (e.g. 'Goa', 'Jaipur')",
        examples=["Goa"],
    )
    departure_city: Optional[str] = Field(
        default=None,
        description="Optional origin or departure city (e.g. 'Delhi', 'BLR')",
        examples=["Delhi"],
    )
    start_date: str = Field(
        ...,
        description="Trip departure date formatted as YYYY-MM-DD",
        examples=["2026-12-15"],
    )
    end_date: str = Field(
        ...,
        description="Trip return/end date formatted as YYYY-MM-DD (can equal start_date for same-day trip)",
        examples=["2026-12-17"],
    )
    adults: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of adult travellers (1-10)",
    )
    children: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="Number of children (int) or list of child ages (0-17)",
    )
    budget: Optional[float] = Field(
        default=None,
        gt=0,
        description="Optional total budget for the trip",
    )
    currency: str = Field(
        default="INR",
        description="3-letter currency code (default: 'INR')",
    )
    interests: List[str] = Field(
        default_factory=list,
        description="List of traveler activity preferences (e.g. ['beach', 'heritage'])",
    )
    pace: str = Field(
        default="moderate",
        description="Travel pace: 'relaxed' (2 stops/day), 'moderate' (3 stops/day), or 'packed' (4 stops/day)",
    )
    max_hotels: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Maximum hotel candidates to return",
    )
    max_flights_per_leg: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum flight options to return per direction (outbound/return)",
    )
    max_places: int = Field(
        default=15,
        ge=3,
        le=30,
        description="Maximum tourist places to return",
    )
    search_radius_meters: int = Field(
        default=15000,
        ge=1000,
        le=50000,
        description="Radius in meters around destination center for attraction discovery",
    )
    enrich_images: bool = Field(
        default=True,
        description="Whether to run Wikimedia image enrichment on places",
    )

    @field_validator("destination", "departure_city")
    @classmethod
    def validate_non_empty_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        if not clean:
            return None
        return clean

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_dates(cls, v: Any) -> str:
        if isinstance(v, date):
            return v.isoformat()
        if not isinstance(v, str):
            raise ValueError("Dates must be formatted as YYYY-MM-DD string.")
        clean = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean):
            raise ValueError("Dates must be formatted as YYYY-MM-DD.")
        try:
            date.fromisoformat(clean)
        except ValueError:
            raise ValueError("Invalid calendar date formatted as YYYY-MM-DD.")
        return clean

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", clean):
            raise ValueError("Currency must be a valid 3-letter ISO code (e.g. 'INR').")
        return clean

    @field_validator("pace")
    @classmethod
    def validate_pace(cls, v: Optional[str]) -> str:
        clean = (v or "").strip().lower()
        if clean in ("relaxed", "slow", "chill", "leisure"):
            return "relaxed"
        if clean in ("packed", "fast", "intense", "busy", "active"):
            return "packed"
        return "moderate"

    @field_validator("children", mode="before")
    @classmethod
    def validate_children(cls, v: Any) -> Optional[List[int]]:
        if v is None:
            return None
        if isinstance(v, bool):
            raise ValueError("children cannot be a boolean.")
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Number of children cannot be negative.")
            if v > 10:
                raise ValueError("Maximum 10 children allowed.")
            return [7] * v
        if isinstance(v, list):
            if len(v) > 10:
                raise ValueError("Maximum 10 children allowed.")
            validated = []
            for item in v:
                if isinstance(item, bool) or not isinstance(item, int):
                    raise ValueError("Child ages must be integers between 0 and 17.")
                if not (0 <= item <= 17):
                    raise ValueError("Child age must be between 0 and 17.")
                validated.append(item)
            return validated
        raise ValueError("children must be an integer count or a list of child ages.")

    @model_validator(mode="after")
    def validate_date_ordering(self) -> "TripAggregationRequest":
        d_start = date.fromisoformat(self.start_date)
        d_end = date.fromisoformat(self.end_date)
        if d_end < d_start:
            raise ValueError("end_date cannot be earlier than start_date.")
        return self

    @property
    def is_same_day(self) -> bool:
        return self.start_date.strip() == self.end_date.strip()

    @property
    def duration_days(self) -> int:
        d_start = date.fromisoformat(self.start_date.strip())
        d_end = date.fromisoformat(self.end_date.strip())
        return (d_end - d_start).days + 1


class TripAggregationResult(BaseModel):
    """Complete aggregated trip data bundle combining independent candidates and diagnostics."""

    destination: str
    destination_coordinates: Optional[GeoCoordinates] = None
    departure_city: Optional[str] = None
    start_date: str
    end_date: str
    duration_days: int
    is_same_day: bool = False
    origin_airports: List[AirportCandidate] = Field(default_factory=list)
    destination_airports: List[AirportCandidate] = Field(default_factory=list)
    outbound_flights: List[AggregatedFlightOption] = Field(default_factory=list)
    return_flights: List[AggregatedFlightOption] = Field(default_factory=list)
    hotels: List[AggregatedHotelOption] = Field(default_factory=list)
    places: List[Place] = Field(default_factory=list)
    places_distance_matrix: Optional[DurationMatrixResponse] = None
    provider_statuses: Dict[str, ProviderExecutionStatus] = Field(default_factory=dict)

