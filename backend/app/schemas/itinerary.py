from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, Field, field_validator

from backend.app.schemas.place import Place
from backend.app.schemas.trip_aggregation import (
    AggregatedFlightOption,
    AggregatedHotelOption,
    TripAggregationRequest,
)


class ItineraryGenerationRequest(TripAggregationRequest):
    """Request schema for complete trip aggregation and itinerary synthesis."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "destination": "Goa",
                "departure_city": "Delhi",
                "start_date": "2026-12-15",
                "end_date": "2026-12-17",
                "adults": 2,
                "budget": 50000.0,
                "currency": "INR",
                "pace": "moderate",
                "interests": ["beach", "heritage"],
            }
        }
    }


class ItineraryStop(BaseModel):
    """A scheduled stop or attraction within a single day plan."""
    stop_number: int = Field(..., ge=1, description="Sequence order of the stop (1, 2, 3...)")
    place_id: str = Field(..., description="Unique ID referencing a verified Place entity")
    name: str = Field(..., description="Name of the attraction")
    category: str = Field(default="tourism.sights", description="Category classification")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None
    image_url: Optional[str] = None
    time_slot: str = Field(..., description="e.g. '09:30 - 11:30'")
    duration_minutes: int = Field(default=90, ge=15)
    travel_from_previous_minutes: float = Field(default=0.0, ge=0.0)
    travel_from_previous_km: float = Field(default=0.0, ge=0.0)
    routing_provider: str = Field(default="osrm", description="'osrm' or 'haversine_estimate'")
    is_estimated_travel: bool = Field(default=False)
    activity_notes: Optional[str] = Field(default=None, description="Concise visit tip or practical note")


class ItineraryDay(BaseModel):
    """Day-wise plan containing sequenced stops and narrative overview."""
    day_number: int = Field(..., ge=1)
    date: str = Field(..., description="YYYY-MM-DD")
    theme_title: str = Field(..., description="Day title/theme (e.g. 'Coastal Forts & Heritage')")
    day_description: str = Field(..., description="Narrative summary of the day's experiences")
    stops: List[ItineraryStop] = Field(default_factory=list)
    total_travel_minutes: float = Field(default=0.0, ge=0.0)
    total_travel_km: float = Field(default=0.0, ge=0.0)


class FlightBookingRecommendation(BaseModel):
    """Recommended flight option selected from aggregator candidates."""
    direction: str = Field(..., description="'outbound' or 'return'")
    flight_id: str
    carrier: str
    origin_iata: str
    destination_iata: str
    departure_date: str
    departure_time: str
    arrival_time: str
    price_amount: float
    currency: str = "INR"
    cabin_class: str = "economy"
    source_provider: str = "Ignav"
    is_indicative: bool = False
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


class HotelBookingRecommendation(BaseModel):
    """Recommended hotel option selected from aggregator candidates."""
    hotel_id: str
    name: str
    star_rating: Optional[int] = None
    user_rating: Optional[float] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    room_name: str
    board_name: str
    total_price: float
    price_per_night: float
    currency: str = "INR"
    is_sandbox: bool = True
    cancellation_policy: Optional[str] = None


class CostBreakdown(BaseModel):
    """Estimated overall trip expenses."""
    flights_cost: Optional[float] = Field(default=None, ge=0.0, description="Total flights cost, or None if unavailable/unknown")
    accommodation_cost: Optional[float] = Field(default=None, ge=0.0, description="Total hotel cost, or None if unavailable/unknown")
    estimated_activities_cost: float = Field(default=0.0, ge=0.0, description="Estimated sightseeing & activities buffer")
    total_estimated_cost: Optional[float] = Field(default=None, ge=0.0, description="Total estimated cost, or None if essential components are unknown")
    currency: str = "INR"
    budget: Optional[float] = None
    is_within_budget: Optional[bool] = None
    is_cost_complete: bool = Field(default=True, description="False if flight or accommodation costs are unknown/missing")


class TripItinerary(BaseModel):
    """Complete synthesized itinerary validated with Pydantic."""
    model_config = {"populate_by_name": True}

    trip_title: str
    destination: str
    departure_city: Optional[str] = None
    start_date: str
    end_date: str
    duration_days: int
    is_same_day: bool = False
    pace: str = "moderate"
    trip_summary: str
    selected_outbound_flight: Optional[FlightBookingRecommendation] = None
    selected_return_flight: Optional[FlightBookingRecommendation] = None
    selected_hotel: Optional[HotelBookingRecommendation] = None
    candidate_outbound_flights: List[AggregatedFlightOption] = Field(
        default_factory=list,
        validation_alias=AliasChoices("candidate_outbound_flights", "outbound_flight_candidates", "outbound_flights"),
        description="All available outbound flight candidates from aggregation",
    )
    candidate_return_flights: List[AggregatedFlightOption] = Field(
        default_factory=list,
        validation_alias=AliasChoices("candidate_return_flights", "return_flight_candidates", "return_flights"),
        description="All available return flight candidates from aggregation",
    )
    candidate_hotels: List[AggregatedHotelOption] = Field(
        default_factory=list,
        validation_alias=AliasChoices("candidate_hotels", "hotel_candidates", "hotels"),
        description="All available hotel candidates from aggregation",
    )
    days: List[ItineraryDay] = Field(default_factory=list)
    cost_breakdown: CostBreakdown
    practical_tips: List[str] = Field(default_factory=list)
    generated_at: str

    @property
    def outbound_flight_candidates(self) -> List[AggregatedFlightOption]:
        return self.candidate_outbound_flights

    @property
    def return_flight_candidates(self) -> List[AggregatedFlightOption]:
        return self.candidate_return_flights

    @property
    def hotel_candidates(self) -> List[AggregatedHotelOption]:
        return self.candidate_hotels


class AddStopAction(BaseModel):
    """Specification for adding a new attraction to a specific day."""
    day_number: int = Field(..., ge=1, description="Target day number (1-indexed)")
    place: Place = Field(..., description="Physical place details with verified coordinates")
    position: Optional[int] = Field(
        default=None,
        ge=1,
        description="Optional 1-indexed insertion position. Appends to the day if omitted or beyond length.",
    )


class ItineraryReplanRequest(BaseModel):
    """Request schema for dynamic itinerary replanning and stop modification."""
    current_itinerary: TripItinerary = Field(..., description="The current itinerary to update")
    remove_place_ids: Optional[List[str]] = Field(
        default=None,
        description="List of place_ids to remove from the itinerary",
    )
    add_stops: Optional[List[AddStopAction]] = Field(
        default=None,
        description="List of new stops to insert into specific days",
    )
    reorder_days: Optional[Dict[int, List[str]]] = Field(
        default=None,
        description="Explicit stop ordering per day: {day_number: [place_id_1, place_id_2, ...]}",
    )
    new_pace: Optional[str] = Field(
        default=None,
        description="Updated pace ('relaxed', 'moderate', or 'packed')",
    )
    new_interests: Optional[List[str]] = Field(
        default=None,
        description="Updated traveler activity interests",
    )
    candidate_places: Optional[List[Place]] = Field(
        default=None,
        description="Optional pool of candidate places for replacements or pace expansion",
    )

    @field_validator("new_pace")
    @classmethod
    def validate_new_pace(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().lower()
        if clean in ("relaxed", "slow", "chill", "leisure"):
            return "relaxed"
        if clean in ("packed", "fast", "intense", "busy", "active"):
            return "packed"
        return "moderate"
