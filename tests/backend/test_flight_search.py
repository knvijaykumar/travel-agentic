from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ignav_service import (
    IgnavService,
    IgnavConfigurationError,
    IgnavAuthenticationError,
    IgnavNetworkError,
    IgnavResponseError,
    get_ignav_service,
)


SAMPLE_FLIGHT_SEARCH_RESPONSE = {
    "origin": "DEL",
    "destination": "GOI",
    "departure_date": "2026-12-01",
    "observed_at": "2026-11-08T12:00:00Z",
    "itineraries": [
        {
            "price": {
                "amount": 4200,
                "currency": "INR",
                "status": "verified",
            },
            "outbound": {
                "carrier": "IndiGo",
                "duration_minutes": 155,
                "segments": [
                    {
                        "marketing_carrier_code": "6E",
                        "flight_number": "6E-205",
                        "departure_airport": "DEL",
                        "arrival_airport": "GOI",
                        "departure_time_local": "2026-12-01T08:00:00",
                        "arrival_time_local": "2026-12-01T10:35:00",
                    }
                ],
            },
            "cabin_class": "economy",
            "has_mixed_carriers": False,
            "ignav_id": "ignav_id_mock_12345",
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


def test_search_flights_success(client):
    """Verify successful POST /api/v1/flights/search calls IgnavService and returns flight response."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.return_value = SAMPLE_FLIGHT_SEARCH_RESPONSE
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
        "adults": 2,
        "cabin_class": "economy",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "DEL"
    assert data["destination"] == "GOI"
    assert data["departure_date"] == "2026-12-01"
    assert len(data["itineraries"]) == 1
    assert data["itineraries"][0]["price"]["amount"] == 4200
    assert data["itineraries"][0]["price"]["currency"] == "INR"
    assert data["itineraries"][0]["ignav_id"] == "ignav_id_mock_12345"

    mock_service.search_one_way_flights.assert_called_once_with(
        origin="DEL",
        destination="GOI",
        departure_date="2026-12-01",
        adults=2,
        cabin_class="economy",
        market="IN",
    )


def test_search_flights_defaults_applied(client):
    """Verify optional fields adults (default 1) and cabin_class (default 'economy') are applied."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.return_value = SAMPLE_FLIGHT_SEARCH_RESPONSE
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 200
    mock_service.search_one_way_flights.assert_called_once_with(
        origin="DEL",
        destination="GOI",
        departure_date="2026-12-01",
        adults=1,
        cabin_class="economy",
        market="IN",
    )


def test_search_flights_lowercase_inputs_normalized(client):
    """Verify lowercase IATA airport codes and cabin class are accepted and normalized."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.return_value = SAMPLE_FLIGHT_SEARCH_RESPONSE
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "del",
        "destination": "goi",
        "departure_date": "2026-12-01",
        "adults": 1,
        "cabin_class": "ECONOMY",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 200
    mock_service.search_one_way_flights.assert_called_once_with(
        origin="DEL",
        destination="GOI",
        departure_date="2026-12-01",
        adults=1,
        cabin_class="economy",
        market="IN",
    )


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {},  # empty body
        {"destination": "GOI", "departure_date": "2026-12-01"},  # missing origin
        {"origin": "DEL", "departure_date": "2026-12-01"},  # missing destination
        {"origin": "DEL", "destination": "GOI"},  # missing departure_date
        {"origin": "DE", "destination": "GOI", "departure_date": "2026-12-01"},  # origin too short
        {"origin": "DELHI", "destination": "GOI", "departure_date": "2026-12-01"},  # origin too long
        {"origin": "123", "destination": "GOI", "departure_date": "2026-12-01"},  # numeric origin
        {"origin": "DEL", "destination": "DEL", "departure_date": "2026-12-01"},  # origin == destination
        {"origin": "DEL", "destination": "GOI", "departure_date": "invalid-date"},  # invalid date format
        {"origin": "DEL", "destination": "GOI", "departure_date": "2026-02-31"},  # invalid calendar date
        {"origin": "DEL", "destination": "GOI", "departure_date": "2026-12-01", "adults": 0},  # adults < 1
        {"origin": "DEL", "destination": "GOI", "departure_date": "2026-12-01", "adults": -1},  # negative adults
        {"origin": "DEL", "destination": "GOI", "departure_date": "2026-12-01", "adults": 10},  # adults > 9
        {"origin": "DEL", "destination": "GOI", "departure_date": "2026-12-01", "cabin_class": "space"},  # invalid cabin
    ],
)
def test_search_flights_invalid_parameters_return_422(client, invalid_payload):
    """Verify invalid request fields fail Pydantic validation with HTTP 422."""
    response = client.post("/api/v1/flights/search", json=invalid_payload)
    assert response.status_code == 422


def test_search_flights_missing_api_key_returns_503(client):
    """Verify missing or unconfigured IGNAV_API_KEY maps to HTTP 503 without leaking credentials."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.side_effect = IgnavConfigurationError(
        "IGNAV_API_KEY is not configured or missing."
    )
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 503
    data = response.json()
    assert "unconfigured or unavailable" in data["detail"].lower()
    assert "key" not in data["detail"].lower()


def test_search_flights_authentication_failure_returns_502(client):
    """Verify upstream Ignav authentication failure (401/403) maps to HTTP 502."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.side_effect = IgnavAuthenticationError(
        "Ignav API authentication failed (HTTP 401): Invalid API key provided"
    )
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 502
    data = response.json()
    assert "authentication failed" in data["detail"].lower()
    # Ensure no API key or sensitive data leaked
    assert "ignav_key" not in data["detail"].lower()


def test_search_flights_network_timeout_returns_504(client):
    """Verify network timeout or connection failure maps to HTTP 504."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.side_effect = IgnavNetworkError(
        "Ignav API request to /fares/one-way timed out."
    )
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 504
    data = response.json()
    assert "timed out or connection failed" in data["detail"].lower()


def test_search_flights_invalid_provider_response_returns_502(client):
    """Verify invalid upstream response (non-JSON or 500 error) maps to HTTP 502."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.side_effect = IgnavResponseError(
        "Invalid JSON response from Ignav /fares/one-way"
    )
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 502
    data = response.json()
    assert "invalid response" in data["detail"].lower()


def test_search_flights_empty_results_returns_200(client):
    """Verify empty flight results return HTTP 200 with empty itineraries list."""
    mock_service = MagicMock(spec=IgnavService)
    empty_result = {
        "origin": "DEL",
        "destination": "IXG",
        "departure_date": "2026-12-01",
        "itineraries": [],
    }
    mock_service.search_one_way_flights.return_value = empty_result
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "IXG",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "DEL"
    assert data["destination"] == "IXG"
    assert data["itineraries"] == []


def test_search_flights_unexpected_exception_returns_500(client):
    """Verify unexpected internal exception returns HTTP 500 without leaking stack traces."""
    mock_service = MagicMock(spec=IgnavService)
    mock_service.search_one_way_flights.side_effect = RuntimeError("Fatal hardware failure")
    app.dependency_overrides[get_ignav_service] = lambda: mock_service

    payload = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-01",
    }

    response = client.post("/api/v1/flights/search", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "unexpected error occurred" in data["detail"].lower()
    assert "Fatal hardware failure" not in data["detail"]

