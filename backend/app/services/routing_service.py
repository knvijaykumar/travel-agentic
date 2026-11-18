import json
import logging
import math
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import (
    DurationMatrixResponse,
    RouteDetail,
    RouteLeg,
)

logger = logging.getLogger(__name__)

DEFAULT_OSRM_BASE_URL = "https://router.project-osrm.org"
ROAD_DETOUR_FACTOR = 1.35  # Empirical road detour factor over straight-line distance
AVERAGE_CITY_SPEED_KMH = 30.0  # Assumed urban/semi-urban average travel speed
DEFAULT_TIMEOUT = 10

_routing_service_instance: Optional["RoutingService"] = None


class RoutingError(Exception):
    """Base exception for routing errors."""
    pass


class RoutingCoordinateError(RoutingError, ValueError):
    """Raised when coordinates are invalid or out of bounds."""
    pass


class OSRMResponseError(RoutingError):
    """Raised when OSRM returns an error code or invalid response."""
    pass


class OSRMNetworkError(RoutingError):
    """Raised when OSRM request times out or encounters network error."""
    pass


def validate_coordinates(lat: float, lon: float, name: str = "Coordinates") -> None:
    """Validate that latitude and longitude are within standard geographical bounds."""
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise RoutingCoordinateError(f"{name}: latitude and longitude must be valid numbers.")

    if not (-90.0 <= lat <= 90.0):
        raise RoutingCoordinateError(f"{name}: latitude {lat} must be between -90.0 and 90.0.")
    if not (-180.0 <= lon <= 180.0):
        raise RoutingCoordinateError(f"{name}: longitude {lon} must be between -180.0 and 180.0.")


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line great-circle distance between two points in meters using Haversine formula."""
    validate_coordinates(lat1, lon1, "Point 1")
    validate_coordinates(lat2, lon2, "Point 2")

    r_earth = 6371000.0  # Earth's mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def estimate_road_distance_and_duration(
    straight_line_meters: float,
    detour_factor: float = ROAD_DETOUR_FACTOR,
    speed_kmh: float = AVERAGE_CITY_SPEED_KMH,
) -> Tuple[float, float]:
    """Estimate road distance (meters) and duration (seconds) using detour factor and average speed."""
    road_meters = straight_line_meters * detour_factor
    speed_mps = (speed_kmh * 1000.0) / 3600.0
    duration_seconds = road_meters / speed_mps if speed_mps > 0 else 0.0
    return road_meters, duration_seconds


class RoutingService:
    """Service to compute route geometry, distance, and duration using OSRM with Haversine fallback."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        configured_url = getattr(settings, "OSRM_BASE_URL", DEFAULT_OSRM_BASE_URL)
        self.base_url = (base_url or configured_url).rstrip("/")
        self.timeout = timeout

    def get_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        fallback_to_haversine: bool = True,
        timeout: Optional[int] = None,
    ) -> RouteDetail:
        """Compute route distance and duration between two coordinates.

        Attempts to query OSRM first. If OSRM is unavailable, falls back to Haversine straight-line
        distance with explicit road detour and duration estimations (clearly labeled as estimates).

        Args:
            origin_lat: Origin latitude (-90 to 90).
            origin_lon: Origin longitude (-180 to 180).
            dest_lat: Destination latitude (-90 to 90).
            dest_lon: Destination longitude (-180 to 180).
            fallback_to_haversine: If True, returns Haversine estimates on OSRM failure (default: True).
            timeout: Network request timeout in seconds.

        Returns:
            RouteDetail with distance, duration, and is_estimated flag.
        """
        validate_coordinates(origin_lat, origin_lon, "Origin")
        validate_coordinates(dest_lat, dest_lon, "Destination")

        straight_line_m = haversine_distance_meters(origin_lat, origin_lon, dest_lat, dest_lon)
        req_timeout = timeout or self.timeout

        # OSRM coordinates format: {lon},{lat}
        url = f"{self.base_url}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"

        osrm_error: Optional[Exception] = None

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "VirtualTravelAgent/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=req_timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)

            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                total_distance_m = float(route.get("distance", 0.0))
                total_duration_s = float(route.get("duration", 0.0))

                legs: List[RouteLeg] = []
                for leg in route.get("legs", []):
                    legs.append(
                        RouteLeg(
                            summary=str(leg.get("summary", "")).strip(),
                            distance_meters=float(leg.get("distance", 0.0)),
                            duration_seconds=float(leg.get("duration", 0.0)),
                            straight_line_distance_meters=round(straight_line_m, 1),
                            is_estimated=False,
                            routing_provider="osrm",
                        )
                    )

                if not legs:
                    legs.append(
                        RouteLeg(
                            summary="OSRM Driving Route",
                            distance_meters=total_distance_m,
                            duration_seconds=total_duration_s,
                            straight_line_distance_meters=round(straight_line_m, 1),
                            is_estimated=False,
                            routing_provider="osrm",
                        )
                    )

                return RouteDetail(
                    total_distance_km=round(total_distance_m / 1000.0, 2),
                    total_duration_minutes=round(total_duration_s / 60.0, 1),
                    geometry_geojson=route.get("geometry"),
                    legs=legs,
                    straight_line_distance_km=round(straight_line_m / 1000.0, 2),
                    is_estimated=False,
                    routing_provider="osrm",
                )
            else:
                osrm_error = OSRMResponseError(
                    f"OSRM returned error code: {data.get('code')}, message: {data.get('message', 'No route')}"
                )

        except urllib.error.HTTPError as exc:
            osrm_error = OSRMResponseError(f"OSRM HTTP error {exc.code}: {exc.reason}")
        except (urllib.error.URLError, TimeoutError) as exc:
            osrm_error = OSRMNetworkError(f"OSRM network error or timeout: {exc}")
        except json.JSONDecodeError as exc:
            osrm_error = OSRMResponseError(f"Invalid JSON response from OSRM: {exc}")
        except Exception as exc:
            osrm_error = OSRMResponseError(f"Unexpected error during OSRM routing: {exc}")

        if not fallback_to_haversine and osrm_error:
            raise osrm_error

        # Haversine Fallback Execution
        logger.warning(
            f"OSRM unavailable ({osrm_error}). Falling back to Haversine distance estimation."
        )

        road_m, dur_s = estimate_road_distance_and_duration(straight_line_m)

        fallback_leg = RouteLeg(
            summary=f"Estimated road route (Haversine fallback: {ROAD_DETOUR_FACTOR}x detour @ {AVERAGE_CITY_SPEED_KMH} km/h)",
            distance_meters=round(road_m, 1),
            duration_seconds=round(dur_s, 1),
            straight_line_distance_meters=round(straight_line_m, 1),
            is_estimated=True,
            routing_provider="haversine_estimate",
        )

        return RouteDetail(
            total_distance_km=round(road_m / 1000.0, 2),
            total_duration_minutes=round(dur_s / 60.0, 1),
            geometry_geojson=None,
            legs=[fallback_leg],
            straight_line_distance_km=round(straight_line_m / 1000.0, 2),
            is_estimated=True,
            routing_provider="haversine_estimate",
        )

    def get_distance_matrix(
        self,
        coordinates: List[GeoCoordinates],
        fallback_to_haversine: bool = True,
        timeout: Optional[int] = None,
    ) -> DurationMatrixResponse:
        """Compute an NxN distance and duration matrix for a list of coordinates.

        Queries OSRM table API. If unavailable, falls back to computing pairwise Haversine
        estimates, clearly marked as estimated.

        Args:
            coordinates: List of GeoCoordinates (minimum 2).
            fallback_to_haversine: If True, returns Haversine estimates on OSRM failure (default: True).
            timeout: Network request timeout in seconds.

        Returns:
            DurationMatrixResponse with durations, distances, and is_estimated flag.
        """
        if not coordinates or len(coordinates) < 2:
            raise RoutingCoordinateError("At least 2 coordinates are required to generate a distance matrix.")

        for idx, coord in enumerate(coordinates):
            validate_coordinates(coord.lat, coord.lon, f"Coordinate [{idx}]")

        req_timeout = timeout or self.timeout
        coords_str = ";".join(f"{c.lon},{c.lat}" for c in coordinates)
        url = f"{self.base_url}/table/v1/driving/{coords_str}?annotations=duration,distance"

        osrm_error: Optional[Exception] = None

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "VirtualTravelAgent/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=req_timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)

            if data.get("code") == "Ok" and "durations" in data:
                durations = data.get("durations", [])
                distances = data.get("distances")

                # Sanitize any null values from OSRM
                clean_durations: List[List[float]] = []
                for row in durations:
                    clean_row = [float(val) if val is not None else 0.0 for val in row]
                    clean_durations.append(clean_row)

                clean_distances: Optional[List[List[float]]] = None
                if distances is not None:
                    clean_distances = []
                    for row in distances:
                        clean_row = [float(val) if val is not None else 0.0 for val in row]
                        clean_distances.append(clean_row)

                return DurationMatrixResponse(
                    durations_seconds=clean_durations,
                    distances_meters=clean_distances,
                    sources=coordinates,
                    destinations=coordinates,
                    is_estimated=False,
                    routing_provider="osrm",
                )
            else:
                osrm_error = OSRMResponseError(
                    f"OSRM table returned error code: {data.get('code')}, message: {data.get('message', 'Failed')}"
                )

        except urllib.error.HTTPError as exc:
            osrm_error = OSRMResponseError(f"OSRM HTTP error {exc.code}: {exc.reason}")
        except (urllib.error.URLError, TimeoutError) as exc:
            osrm_error = OSRMNetworkError(f"OSRM network error or timeout: {exc}")
        except json.JSONDecodeError as exc:
            osrm_error = OSRMResponseError(f"Invalid JSON response from OSRM table: {exc}")
        except Exception as exc:
            osrm_error = OSRMResponseError(f"Unexpected error during OSRM table matrix: {exc}")

        if not fallback_to_haversine and osrm_error:
            raise osrm_error

        # Haversine Fallback Matrix
        logger.warning(
            f"OSRM table unavailable ({osrm_error}). Generating Haversine fallback matrix."
        )

        n = len(coordinates)
        durations_matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
        distances_matrix: List[List[float]] = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    c_i = coordinates[i]
                    c_j = coordinates[j]
                    s_m = haversine_distance_meters(c_i.lat, c_i.lon, c_j.lat, c_j.lon)
                    road_m, dur_s = estimate_road_distance_and_duration(s_m)
                    distances_matrix[i][j] = round(road_m, 1)
                    durations_matrix[i][j] = round(dur_s, 1)

        return DurationMatrixResponse(
            durations_seconds=durations_matrix,
            distances_meters=distances_matrix,
            sources=coordinates,
            destinations=coordinates,
            is_estimated=True,
            routing_provider="haversine_estimate",
        )


def get_routing_service() -> RoutingService:
    """Singleton provider for the RoutingService."""
    global _routing_service_instance
    if _routing_service_instance is None:
        _routing_service_instance = RoutingService()
    return _routing_service_instance

