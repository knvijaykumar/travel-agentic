from typing import List, Optional
from pydantic import BaseModel, Field


class HotelOffer(BaseModel):
    """Normalized Hotel Offer model from Accommodation integration."""
    id: str
    name: str
    city_code: str
    rating: Optional[float] = 4.0
    price_per_night: float
    currency: str = "USD"
    address: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    check_in: str
    check_out: str
    booking_url: Optional[str] = None


class FlightOffer(BaseModel):
    """Normalized Flight Offer model from Transport integration."""
    id: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    carrier_name: str
    carrier_code: str
    flight_number: str
    price: float
    currency: str = "USD"
    stops: int = 0
    cabin_class: str = "ECONOMY"


class HotelSearchQuery(BaseModel):
    city_code: str
    check_in_date: str = "2026-12-01"
    check_out_date: str = "2026-12-04"
    guests: int = 1
    max_price: Optional[float] = None


class FlightSearchQuery(BaseModel):
    origin: str
    destination: str
    departure_date: str = "2026-12-01"
    return_date: Optional[str] = None
    adults: int = 1
    max_price: Optional[float] = None
