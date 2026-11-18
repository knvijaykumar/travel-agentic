from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.places import GeoCoordinates


class DurationMatrixRequest(BaseModel):
    """Request coordinates to generate an NxN duration matrix."""
    coordinates: List[GeoCoordinates] = Field(..., min_length=2)


class DurationMatrixResponse(BaseModel):
    """Distance and duration matrix between N locations from OSRM or Haversine fallback."""
    durations_seconds: List[List[float]]
    distances_meters: Optional[List[List[float]]] = None
    sources: List[GeoCoordinates]
    destinations: List[GeoCoordinates]
    is_estimated: bool = Field(default=False, description="True if values are Haversine estimates")
    routing_provider: str = Field(default="osrm", description="'osrm' or 'haversine_estimate'")


class RouteLeg(BaseModel):
    summary: str = ""
    distance_meters: float
    duration_seconds: float
    straight_line_distance_meters: Optional[float] = None
    is_estimated: bool = Field(default=False, description="True if values are Haversine estimates")
    routing_provider: str = Field(default="osrm", description="'osrm' or 'haversine_estimate'")


class RouteDetail(BaseModel):
    """Route geometry and navigation detail between scheduled points."""
    total_distance_km: float
    total_duration_minutes: float
    geometry_geojson: Optional[dict] = None
    polyline: Optional[str] = None
    legs: List[RouteLeg] = Field(default_factory=list)
    straight_line_distance_km: Optional[float] = None
    is_estimated: bool = Field(default=False, description="True if values are Haversine estimates")
    routing_provider: str = Field(default="osrm", description="'osrm' or 'haversine_estimate'")

