import io
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import DurationMatrixResponse, RouteDetail
from backend.app.services.routing_service import (
    RoutingService,
    RoutingCoordinateError,
    OSRMNetworkError,
    OSRMResponseError,
    haversine_distance_meters,
    estimate_road_distance_and_duration,
    get_routing_service,
)


SAMPLE_OSRM_ROUTE_RESPONSE = {
    "code": "Ok",
    "routes": [
        {
            "distance": 18500.5,
            "duration": 1820.0,
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [73.8278, 15.4989],
                    [73.8100, 15.4950],
                    [73.7736, 15.4925],
                ],
            },
            "legs": [
                {
                    "distance": 18500.5,
                    "duration": 1820.0,
                    "summary": "NH 66, Aguada-Siolim Rd",
                }
            ],
        }
    ],
    "waypoints": [
        {"name": "Panaji", "location": [73.8278, 15.4989]},
        {"name": "Fort Aguada", "location": [73.7736, 15.4925]},
    ],
}

SAMPLE_OSRM_TABLE_RESPONSE = {
    "code": "Ok",
    "durations": [
        [0.0, 1820.0, 2450.0],
        [1800.0, 0.0, 1100.0],
        [2400.0, 1120.0, 0.0],
    ],
    "distances": [
        [0.0, 18500.0, 25000.0],
        [18400.0, 0.0, 12000.0],
        [24800.0, 12100.0, 0.0],
    ],
    "sources": [{"location": [73.8, 15.5]}, {"location": [73.7, 15.4]}, {"location": [73.9, 15.6]}],
    "destinations": [{"location": [73.8, 15.5]}, {"location": [73.7, 15.4]}, {"location": [73.9, 15.6]}],
}


def create_mock_http_response(data: dict, status_code: int = 200):
    """Helper to mock urllib.request.urlopen response."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = status_code
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


# ──────────────────────────────────────────────────────────────────
#  Haversine & Road Estimation Math
# ──────────────────────────────────────────────────────────────────

def test_haversine_distance_calculation():
    """Verify Haversine formula accurately calculates known distance between Panaji and Aguada Fort (~5.8 km)."""
    # Panaji (15.4989, 73.8278) -> Fort Aguada (15.4925, 73.7736)
    dist = haversine_distance_meters(15.4989, 73.8278, 15.4925, 73.7736)
    assert 5500 < dist < 6200  # ~5.8 km straight line


def test_haversine_identical_points_returns_zero():
    """Verify identical coordinates yield 0 distance."""
    dist = haversine_distance_meters(26.9196, 75.8189, 26.9196, 75.8189)
    assert dist == pytest.approx(0.0)


def test_road_distance_and_duration_estimation():
    """Verify road distance applies 1.35x detour factor and duration assumes 30 km/h."""
    straight_line = 10000.0  # 10 km
    road_m, dur_s = estimate_road_distance_and_duration(straight_line, detour_factor=1.35, speed_kmh=30.0)

    assert road_m == pytest.approx(13500.0)  # 13.5 km
    # 13.5 km at 30 km/h = 0.45 hours = 27 minutes = 1620 seconds
    assert dur_s == pytest.approx(1620.0)


# ──────────────────────────────────────────────────────────────────
#  OSRM Route Calculation (Success & Distinction)
# ──────────────────────────────────────────────────────────────────

def test_get_route_osrm_success():
    """Verify successful OSRM query returns RouteDetail labeled as osrm, not estimated."""
    service = RoutingService()
    mock_resp = create_mock_http_response(SAMPLE_OSRM_ROUTE_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        route = service.get_route(
            origin_lat=15.4989,
            origin_lon=73.8278,
            dest_lat=15.4925,
            dest_lon=73.7736,
        )

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        # OSRM lon,lat ordering in URL
        assert "73.8278,15.4989;73.7736,15.4925" in req.full_url

        assert isinstance(route, RouteDetail)
        assert route.is_estimated is False
        assert route.routing_provider == "osrm"
        assert route.total_distance_km == pytest.approx(18.5, rel=1e-2)
        assert route.total_duration_minutes == pytest.approx(30.3, rel=1e-2)
        assert route.straight_line_distance_km is not None
        assert route.geometry_geojson is not None
        assert len(route.legs) == 1
        assert route.legs[0].is_estimated is False
        assert route.legs[0].routing_provider == "osrm"
        assert route.legs[0].summary == "NH 66, Aguada-Siolim Rd"


# ──────────────────────────────────────────────────────────────────
#  Haversine Fallback Handling
# ──────────────────────────────────────────────────────────────────

def test_get_route_osrm_timeout_triggers_haversine_fallback():
    """Verify timeout triggers Haversine fallback, clearly labeled as estimate and not OSRM."""
    service = RoutingService()

    with patch("urllib.request.urlopen", side_effect=TimeoutError("OSRM timed out")):
        route = service.get_route(
            origin_lat=15.4989,
            origin_lon=73.8278,
            dest_lat=15.4925,
            dest_lon=73.7736,
            fallback_to_haversine=True,
        )

        assert isinstance(route, RouteDetail)
        assert route.is_estimated is True
        assert route.routing_provider == "haversine_estimate"
        assert route.routing_provider != "osrm"
        assert route.total_distance_km > 0
        assert route.total_duration_minutes > 0
        assert route.straight_line_distance_km is not None
        # Road distance should exceed straight-line distance due to detour factor
        assert route.total_distance_km > route.straight_line_distance_km
        assert len(route.legs) == 1
        assert route.legs[0].is_estimated is True
        assert "Haversine fallback" in route.legs[0].summary


def test_get_route_osrm_http_error_triggers_haversine_fallback():
    """Verify HTTP 500 error triggers Haversine fallback."""
    service = RoutingService()
    http_err = urllib.error.HTTPError(
        url="https://router.project-osrm.org",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(b'{"message": "OSRM routing failed"}'),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        route = service.get_route(
            origin_lat=15.4989,
            origin_lon=73.8278,
            dest_lat=15.4925,
            dest_lon=73.7736,
            fallback_to_haversine=True,
        )

        assert route.is_estimated is True
        assert route.routing_provider == "haversine_estimate"


def test_get_route_osrm_error_without_fallback_raises_exception():
    """Verify fallback_to_haversine=False raises typed OSRMNetworkError on network failure."""
    service = RoutingService()

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        with pytest.raises(OSRMNetworkError):
            service.get_route(
                origin_lat=15.4989,
                origin_lon=73.8278,
                dest_lat=15.4925,
                dest_lon=73.7736,
                fallback_to_haversine=False,
            )


# ──────────────────────────────────────────────────────────────────
#  Distance Matrix
# ──────────────────────────────────────────────────────────────────

def test_get_distance_matrix_osrm_success():
    """Verify successful OSRM table query returns DurationMatrixResponse labeled as osrm."""
    service = RoutingService()
    mock_resp = create_mock_http_response(SAMPLE_OSRM_TABLE_RESPONSE)

    coords = [
        GeoCoordinates(lat=15.5, lon=73.8),
        GeoCoordinates(lat=15.4, lon=73.7),
        GeoCoordinates(lat=15.6, lon=73.9),
    ]

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        matrix = service.get_distance_matrix(coords)

        assert mock_urlopen.called
        assert isinstance(matrix, DurationMatrixResponse)
        assert matrix.is_estimated is False
        assert matrix.routing_provider == "osrm"
        assert len(matrix.durations_seconds) == 3
        assert len(matrix.distances_meters) == 3
        assert matrix.durations_seconds[0][1] == 1820.0
        assert matrix.distances_meters[0][1] == 18500.0


def test_get_distance_matrix_osrm_failure_triggers_haversine_fallback():
    """Verify OSRM table failure generates full pairwise Haversine matrix clearly labeled as estimate."""
    service = RoutingService()

    coords = [
        GeoCoordinates(lat=15.5, lon=73.8),
        GeoCoordinates(lat=15.4, lon=73.7),
        GeoCoordinates(lat=15.6, lon=73.9),
    ]

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Matrix timed out")):
        matrix = service.get_distance_matrix(coords, fallback_to_haversine=True)

        assert isinstance(matrix, DurationMatrixResponse)
        assert matrix.is_estimated is True
        assert matrix.routing_provider == "haversine_estimate"
        assert len(matrix.durations_seconds) == 3
        assert len(matrix.distances_meters) == 3
        # Diagonals must be 0
        assert matrix.durations_seconds[0][0] == 0.0
        assert matrix.distances_meters[0][0] == 0.0
        # Off-diagonals must be positive
        assert matrix.distances_meters[0][1] > 0.0
        assert matrix.durations_seconds[0][1] > 0.0


# ──────────────────────────────────────────────────────────────────
#  Validation Errors
# ──────────────────────────────────────────────────────────────────

def test_get_route_invalid_coordinates():
    """Verify coordinates outside valid geographical bounds raise RoutingCoordinateError."""
    service = RoutingService()

    with pytest.raises(RoutingCoordinateError, match="latitude"):
        service.get_route(origin_lat=95.0, origin_lon=73.8, dest_lat=15.4, dest_lon=73.7)

    with pytest.raises(RoutingCoordinateError, match="longitude"):
        service.get_route(origin_lat=15.5, origin_lon=-190.0, dest_lat=15.4, dest_lon=73.7)


def test_get_distance_matrix_too_few_coordinates():
    """Verify fewer than 2 coordinates raises RoutingCoordinateError."""
    service = RoutingService()

    with pytest.raises(RoutingCoordinateError, match="At least 2 coordinates"):
        service.get_distance_matrix([])

    with pytest.raises(RoutingCoordinateError, match="At least 2 coordinates"):
        service.get_distance_matrix([GeoCoordinates(lat=15.5, lon=73.8)])


# ──────────────────────────────────────────────────────────────────
#  Singleton Provider
# ──────────────────────────────────────────────────────────────────

def test_get_routing_service_singleton():
    """Verify get_routing_service returns the same singleton instance."""
    s1 = get_routing_service()
    s2 = get_routing_service()
    assert s1 is s2
    assert isinstance(s1, RoutingService)

