from typing import List, Optional
from pydantic import BaseModel, Field


class GeoCoordinates(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")


class PlaceItem(BaseModel):
    """Normalized Place/Attraction entity from OpenStreetMap & Wikimedia."""
    id: str
    name: str
    category: str = "sightseeing"
    lat: float
    lon: float
    rating: Optional[float] = 4.5
    address: Optional[str] = None
    opening_time: Optional[str] = "09:00"
    closing_time: Optional[str] = "18:00"
    estimated_duration_minutes: int = 90
    estimated_cost: float = 0.0
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class PlaceSearchQuery(BaseModel):
    city: str
    category: Optional[str] = None
    limit: int = 15
