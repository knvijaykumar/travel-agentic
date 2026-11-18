from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.nuitee_service import (
    NuiteeService,
    NuiteeConfigurationError,
    NuiteeAuthenticationError,
    NuiteeNetworkError,
    NuiteeResponseError,
    get_nuitee_service,
)


SAMPLE_HOTEL_SEARCH_RESPONSE = {
    "data": [
        {
            "hotelId": "lp1a2b3c",
            "roomTypes": [
                {
                    "offerId": "offer_abc123",
                    "rates": [
                        {
                            "name": "Deluxe Room",
                            "boardName": "Room Only",
                            "retailRate": {
                                "total": [
                                    {"amount": 5200.00, "currency": "INR"}
                                ]
                            },
                        }
                    ],
                }
            ],
        }
    ],
    "hotels": [
        {
            "id": "lp1a2b3c",
            "name": "Taj Mahal Palace",
            "starRating": 5,
            "main_photo": "https://photos.liteapi.travel/taj_palace.jpg",
            "address": "Apollo Bunder, Colaba, Mumbai",
            "rating": 9.2,
            "location": {"latitude": 18.9217, "longitude": 72.8332},
        }
    ],
}


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Clear FastAPI dependency overrides before and after each test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────
#  Successful Search Cases
# ──────────────────────────────────────────────────────────────────

def test_search_hotels_city_success(client):
    """Verify successful POST /api/v1/hotels/search with city and country code."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.return_value = SAMPLE_HOTEL_SEARCH_RESPONSE
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Mumbai",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
        "adults": 2,
        "children": [5],
        "currency": "INR",
        "guest_nationality": "IN",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["hotelId"] == "lp1a2b3c"
    assert len(data["hotels"]) == 1
    assert data["hotels"][0]["name"] == "Taj Mahal Palace"

    mock_service.search_hotel_rates.assert_called_once_with(
        checkin="2026-12-20",
        checkout="2026-12-22",
        occupancies=[{"adults": 2, "children": [5]}],
        adults=2,
        currency="INR",
        guest_nationality="IN",
        city_name="Mumbai",
        country_code="IN",
        latitude=None,
        longitude=None,
        radius=None,
        hotel_ids=None,
        include_hotel_data=True,
    )


def test_search_hotels_coordinate_success(client):
    """Verify successful hotel search with latitude, longitude, and optional radius."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.return_value = SAMPLE_HOTEL_SEARCH_RESPONSE
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "latitude": 18.9217,
        "longitude": 72.8332,
        "radius": 15,
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 200
    mock_service.search_hotel_rates.assert_called_once_with(
        checkin="2026-12-20",
        checkout="2026-12-22",
        occupancies=[{"adults": 1, "children": []}],
        adults=1,
        currency="INR",
        guest_nationality="IN",
        city_name=None,
        country_code=None,
        latitude=18.9217,
        longitude=72.8332,
        radius=15,
        hotel_ids=None,
        include_hotel_data=True,
    )


def test_search_hotels_hotel_ids_success(client):
    """Verify successful hotel search with explicit hotel_ids."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.return_value = SAMPLE_HOTEL_SEARCH_RESPONSE
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "hotel_ids": ["lp1a2b3c", "lp4d5e6f"],
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 200
    mock_service.search_hotel_rates.assert_called_once_with(
        checkin="2026-12-20",
        checkout="2026-12-22",
        occupancies=[{"adults": 1, "children": []}],
        adults=1,
        currency="INR",
        guest_nationality="IN",
        city_name=None,
        country_code=None,
        latitude=None,
        longitude=None,
        radius=None,
        hotel_ids=["lp1a2b3c", "lp4d5e6f"],
        include_hotel_data=True,
    )


def test_search_hotels_defaults_applied(client):
    """Verify default currency (INR), nationality (IN), and adults (1) are applied."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.return_value = SAMPLE_HOTEL_SEARCH_RESPONSE
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Bengaluru",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 200
    mock_service.search_hotel_rates.assert_called_once_with(
        checkin="2026-12-20",
        checkout="2026-12-22",
        occupancies=[{"adults": 1, "children": []}],
        adults=1,
        currency="INR",
        guest_nationality="IN",
        city_name="Bengaluru",
        country_code="IN",
        latitude=None,
        longitude=None,
        radius=None,
        hotel_ids=None,
        include_hotel_data=True,
    )


def test_search_hotels_aliases_and_normalization(client):
    """Verify camelCase aliases and lowercase normalization work seamlessly."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.return_value = SAMPLE_HOTEL_SEARCH_RESPONSE
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "cityName": "Goa",
        "countryCode": "in",
        "check_in": "2026-12-20",
        "check_out": "2026-12-22",
        "currency": "inr",
        "guestNationality": "in",
        "children": 2,  # integer count converted to [7, 7]
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 200
    mock_service.search_hotel_rates.assert_called_once_with(
        checkin="2026-12-20",
        checkout="2026-12-22",
        occupancies=[{"adults": 1, "children": [7, 7]}],
        adults=1,
        currency="INR",
        guest_nationality="IN",
        city_name="Goa",
        country_code="IN",
        latitude=None,
        longitude=None,
        radius=None,
        hotel_ids=None,
        include_hotel_data=True,
    )


def test_search_hotels_empty_results_returns_200(client):
    """Verify empty hotel results return HTTP 200 with empty lists."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.return_value = {"data": [], "hotels": []}
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "UnknownCity",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["hotels"] == []


# ──────────────────────────────────────────────────────────────────
#  Validation Errors (HTTP 422)
# ──────────────────────────────────────────────────────────────────

def test_search_hotels_missing_location_filter_returns_422(client):
    """Verify request with no location filter returns HTTP 422."""
    payload = {
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }
    response = client.post("/api/v1/hotels/search", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "incomplete_payload",
    [
        {"city_name": "Mumbai", "checkin": "2026-12-20", "checkout": "2026-12-22"},  # missing country_code
        {"country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22"},  # missing city_name
        {"latitude": 18.9, "checkin": "2026-12-20", "checkout": "2026-12-22"},  # missing longitude
        {"longitude": 72.8, "checkin": "2026-12-20", "checkout": "2026-12-22"},  # missing latitude
        {"radius": 10, "checkin": "2026-12-20", "checkout": "2026-12-22"},  # radius without coords
    ],
)
def test_search_hotels_incomplete_location_returns_422(client, incomplete_payload):
    """Verify incomplete location parameters return HTTP 422."""
    response = client.post("/api/v1/hotels/search", json=incomplete_payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "conflicting_payload",
    [
        # city + coords
        {
            "city_name": "Mumbai",
            "country_code": "IN",
            "latitude": 18.9,
            "longitude": 72.8,
            "checkin": "2026-12-20",
            "checkout": "2026-12-22",
        },
        # city + hotel_ids
        {
            "city_name": "Mumbai",
            "country_code": "IN",
            "hotel_ids": ["lp1a2b3c"],
            "checkin": "2026-12-20",
            "checkout": "2026-12-22",
        },
        # coords + hotel_ids
        {
            "latitude": 18.9,
            "longitude": 72.8,
            "hotel_ids": ["lp1a2b3c"],
            "checkin": "2026-12-20",
            "checkout": "2026-12-22",
        },
    ],
)
def test_search_hotels_conflicting_locations_return_422(client, conflicting_payload):
    """Verify conflicting location filters return HTTP 422."""
    response = client.post("/api/v1/hotels/search", json=conflicting_payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_date_payload",
    [
        # checkout before checkin
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-22", "checkout": "2026-12-20"},
        # checkout equal to checkin
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-20"},
        # invalid format
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "invalid", "checkout": "2026-12-20"},
        # invalid calendar date
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-02-30", "checkout": "2026-12-20"},
        # missing checkout
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20"},
        # missing checkin
        {"city_name": "Mumbai", "country_code": "IN", "checkout": "2026-12-22"},
    ],
)
def test_search_hotels_invalid_dates_return_422(client, invalid_date_payload):
    """Verify invalid date combinations and formats return HTTP 422."""
    response = client.post("/api/v1/hotels/search", json=invalid_date_payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_occupancy_payload",
    [
        # adults < 1
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "adults": 0},
        # adults negative
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "adults": -1},
        # adults > 20
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "adults": 25},
        # negative children count
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "children": -1},
        # invalid child age (< 0)
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "children": [-1]},
        # invalid child age (> 17)
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "children": [18]},
        # invalid child type
        {"city_name": "Mumbai", "country_code": "IN", "checkin": "2026-12-20", "checkout": "2026-12-22", "children": "two"},
    ],
)
def test_search_hotels_invalid_occupancy_returns_422(client, invalid_occupancy_payload):
    """Verify invalid occupancy settings return HTTP 422."""
    response = client.post("/api/v1/hotels/search", json=invalid_occupancy_payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_coord_payload",
    [
        # latitude > 90
        {"latitude": 91.0, "longitude": 72.8, "checkin": "2026-12-20", "checkout": "2026-12-22"},
        # latitude < -90
        {"latitude": -91.0, "longitude": 72.8, "checkin": "2026-12-20", "checkout": "2026-12-22"},
        # longitude > 180
        {"latitude": 18.9, "longitude": 185.0, "checkin": "2026-12-20", "checkout": "2026-12-22"},
        # longitude < -180
        {"latitude": 18.9, "longitude": -185.0, "checkin": "2026-12-20", "checkout": "2026-12-22"},
        # radius <= 0
        {"latitude": 18.9, "longitude": 72.8, "radius": 0, "checkin": "2026-12-20", "checkout": "2026-12-22"},
        {"latitude": 18.9, "longitude": 72.8, "radius": -5, "checkin": "2026-12-20", "checkout": "2026-12-22"},
    ],
)
def test_search_hotels_invalid_coordinates_return_422(client, invalid_coord_payload):
    """Verify out-of-range coordinates and radius return HTTP 422."""
    response = client.post("/api/v1/hotels/search", json=invalid_coord_payload)
    assert response.status_code == 422


# ──────────────────────────────────────────────────────────────────
#  Upstream & Error Handling (HTTP 502, 503, 504, 500)
# ──────────────────────────────────────────────────────────────────

def test_search_hotels_missing_api_key_returns_503(client):
    """Verify missing NUITEE_API_KEY maps to HTTP 503 without leaking credentials."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.side_effect = NuiteeConfigurationError(
        "NUITEE_API_KEY is not configured or missing."
    )
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Mumbai",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 503
    data = response.json()
    assert "unconfigured or unavailable" in data["detail"].lower()
    assert "key" not in data["detail"].lower()


def test_search_hotels_authentication_failure_returns_502(client):
    """Verify upstream Nuitee authentication failure (401/403) maps to HTTP 502."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.side_effect = NuiteeAuthenticationError(
        "Nuitee API authentication failed (HTTP 401): Invalid API key"
    )
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Mumbai",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 502
    data = response.json()
    assert "authentication failed" in data["detail"].lower()
    assert "nuitee_key" not in data["detail"].lower()


def test_search_hotels_network_timeout_returns_504(client):
    """Verify network timeout or connection failure maps to HTTP 504."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.side_effect = NuiteeNetworkError(
        "Nuitee API request to /hotels/rates timed out."
    )
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Mumbai",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 504
    data = response.json()
    assert "timed out or connection failed" in data["detail"].lower()


def test_search_hotels_invalid_provider_response_returns_502(client):
    """Verify upstream provider invalid response (e.g. 500 error or corrupt JSON) maps to HTTP 502."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.side_effect = NuiteeResponseError(
        "Invalid JSON response from Nuitee /hotels/rates"
    )
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Mumbai",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 502
    data = response.json()
    assert "invalid response" in data["detail"].lower()


def test_search_hotels_unexpected_exception_returns_500(client):
    """Verify unexpected internal exception returns HTTP 500 without leaking stack traces."""
    mock_service = MagicMock(spec=NuiteeService)
    mock_service.search_hotel_rates.side_effect = RuntimeError("Disk read error on cluster")
    app.dependency_overrides[get_nuitee_service] = lambda: mock_service

    payload = {
        "city_name": "Mumbai",
        "country_code": "IN",
        "checkin": "2026-12-20",
        "checkout": "2026-12-22",
    }

    response = client.post("/api/v1/hotels/search", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "unexpected error occurred" in data["detail"].lower()
    assert "Disk read error" not in data["detail"]

