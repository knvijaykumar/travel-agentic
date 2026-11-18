import io
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.ignav_service import (
    IgnavService,
    IgnavError,
    IgnavAuthenticationError,
    IgnavNetworkError,
    IgnavResponseError,
    get_ignav_service,
)


SAMPLE_AIRPORTS_RESPONSE = [
    {
        "iata": "DEL",
        "name": "Indira Gandhi International Airport",
        "city": "New Delhi",
        "country": "India",
        "timezone": "Asia/Kolkata",
    },
    {
        "iata": "BOM",
        "name": "Chhatrapati Shivaji Maharaj International Airport",
        "city": "Mumbai",
        "country": "India",
        "timezone": "Asia/Kolkata",
    },
]

SAMPLE_FLIGHTS_RESPONSE = {
    "origin": "DEL",
    "destination": "GOI",
    "departure_date": "2026-12-01",
    "observed_at": "2026-11-01T10:00:00Z",
    "itineraries": [
        {
            "price": {
                "amount": 4500,
                "currency": "INR",
                "status": "verified",
            },
            "outbound": {
                "carrier": "IndiGo",
                "duration_minutes": 150,
                "segments": [
                    {
                        "marketing_carrier_code": "6E",
                        "flight_number": "6E-205",
                        "departure_airport": "DEL",
                        "arrival_airport": "GOI",
                        "departure_time_local": "2026-12-01T08:00:00",
                        "arrival_time_local": "2026-12-01T10:30:00",
                    }
                ],
            },
            "cabin_class": "economy",
            "has_mixed_carriers": False,
            "ignav_id": "ignav_offer_12345",
        }
    ],
}


def create_mock_http_response(data: any, status_code: int = 200) -> MagicMock:
    """Helper to mock urllib.request.urlopen response."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = status_code
    if isinstance(data, (dict, list)):
        mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    elif isinstance(data, str):
        mock_resp.read.return_value = data.encode("utf-8")
    elif isinstance(data, bytes):
        mock_resp.read.return_value = data
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


def test_search_airports_success():
    """Verify successful airport search returns parsed airport dictionaries and sends correct headers."""
    service = IgnavService(api_key="test_api_key_123")
    mock_resp = create_mock_http_response(SAMPLE_AIRPORTS_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        airports = service.search_airports(query="Delhi", limit=5)

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        assert req.get_method() == "GET"
        assert req.get_header("X-api-key") == "test_api_key_123"
        assert "q=Delhi" in req.full_url
        assert "limit=5" in req.full_url

        assert isinstance(airports, list)
        assert len(airports) == 2
        assert airports[0]["iata"] == "DEL"
        assert airports[0]["name"] == "Indira Gandhi International Airport"
        assert airports[1]["iata"] == "BOM"


def test_search_airports_empty_query_returns_empty_list():
    """Verify empty or whitespace query returns an empty list without making an API request."""
    service = IgnavService(api_key="test_api_key_123")
    with patch("urllib.request.urlopen") as mock_urlopen:
        assert service.search_airports("") == []
        assert service.search_airports("   ") == []
        assert not mock_urlopen.called


def test_search_one_way_flights_success():
    """Verify successful one-way flight search sends POST payload with market='IN' and correct auth."""
    service = IgnavService(api_key="test_api_key_123")
    mock_resp = create_mock_http_response(SAMPLE_FLIGHTS_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = service.search_one_way_flights(
            origin="DEL",
            destination="GOI",
            departure_date="2026-12-01",
            adults=2,
            cabin_class="economy",
        )

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        assert req.get_method() == "POST"
        assert req.get_header("X-api-key") == "test_api_key_123"
        assert req.get_header("Content-type") == "application/json"

        # Verify POST body payload
        body = json.loads(req.data.decode("utf-8"))
        assert body["origin"] == "DEL"
        assert body["destination"] == "GOI"
        assert body["departure_date"] == "2026-12-01"
        assert body["adults"] == 2
        assert body["cabin_class"] == "economy"
        assert body["market"] == "IN"

        # Verify parsed response
        assert isinstance(result, dict)
        assert result["origin"] == "DEL"
        assert result["destination"] == "GOI"
        assert len(result["itineraries"]) == 1
        itinerary = result["itineraries"][0]
        assert itinerary["price"]["amount"] == 4500
        assert itinerary["price"]["currency"] == "INR"
        assert itinerary["ignav_id"] == "ignav_offer_12345"


def test_search_one_way_flights_missing_required_params():
    """Verify missing required parameters (origin, destination, date) raise ValueError."""
    service = IgnavService(api_key="test_api_key_123")
    with pytest.raises(ValueError, match="origin, destination, and departure_date are required"):
        service.search_one_way_flights("", "GOI", "2026-12-01")
    with pytest.raises(ValueError, match="origin, destination, and departure_date are required"):
        service.search_one_way_flights("DEL", "", "2026-12-01")
    with pytest.raises(ValueError, match="origin, destination, and departure_date are required"):
        service.search_one_way_flights("DEL", "GOI", "")


def test_missing_api_key_raises_authentication_error():
    """Verify that attempting to call API without an API key raises IgnavAuthenticationError."""
    service = IgnavService(api_key="")
    with pytest.raises(IgnavAuthenticationError, match="IGNAV_API_KEY is not configured or missing"):
        service.search_airports("DEL")

    with pytest.raises(IgnavAuthenticationError, match="IGNAV_API_KEY is not configured or missing"):
        service.search_one_way_flights("DEL", "GOI", "2026-12-01")


def test_authentication_failure_http_401():
    """Verify HTTP 401 Unauthorized raises IgnavAuthenticationError without exposing secrets."""
    service = IgnavService(api_key="invalid_or_expired_key")
    error_body = json.dumps({"error": "Invalid API key provided"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://ignav.com/api/fares/one-way",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(error_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(IgnavAuthenticationError) as exc_info:
            service.search_one_way_flights("DEL", "GOI", "2026-12-01")

        assert "authentication failed" in str(exc_info.value).lower()
        assert "401" in str(exc_info.value)
        # Ensure secret key does not appear in exception message
        assert "invalid_or_expired_key" not in str(exc_info.value)


def test_authentication_failure_http_403():
    """Verify HTTP 403 Forbidden raises IgnavAuthenticationError."""
    service = IgnavService(api_key="forbidden_key")
    error_body = json.dumps({"message": "Forbidden access"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://ignav.com/api/airports",
        code=403,
        msg="Forbidden",
        hdrs={},
        fp=io.BytesIO(error_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(IgnavAuthenticationError) as exc_info:
            service.search_airports("BOM")

        assert "403" in str(exc_info.value)


def test_network_timeout_handling():
    """Verify network timeout raises IgnavNetworkError."""
    service = IgnavService(api_key="test_api_key_123")

    # Subcase A: standard TimeoutError
    with patch("urllib.request.urlopen", side_effect=TimeoutError("The read operation timed out")):
        with pytest.raises(IgnavNetworkError, match="timed out"):
            service.search_airports("DEL")

    # Subcase B: URLError with timeout reason
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection timed out")):
        with pytest.raises(IgnavNetworkError, match="timed out"):
            service.search_one_way_flights("DEL", "GOI", "2026-12-01")


def test_network_connection_failure():
    """Verify connection refused raises IgnavNetworkError."""
    service = IgnavService(api_key="test_api_key_123")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        with pytest.raises(IgnavNetworkError, match="Connection refused"):
            service.search_airports("DEL")


def test_invalid_api_response_non_json():
    """Verify non-JSON response (e.g., HTML 502 page) raises IgnavResponseError."""
    service = IgnavService(api_key="test_api_key_123")
    mock_resp = create_mock_http_response("<html><body>502 Bad Gateway</body></html>")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(IgnavResponseError, match="Invalid JSON response"):
            service.search_airports("DEL")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(IgnavResponseError, match="Invalid JSON response"):
            service.search_one_way_flights("DEL", "GOI", "2026-12-01")


def test_invalid_api_response_http_500():
    """Verify HTTP 500 Internal Server Error raises IgnavResponseError."""
    service = IgnavService(api_key="test_api_key_123")
    error_body = json.dumps({"error": "Internal server error"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://ignav.com/api/fares/one-way",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(error_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(IgnavResponseError) as exc_info:
            service.search_one_way_flights("DEL", "GOI", "2026-12-01")
        assert "500" in str(exc_info.value)


def test_empty_flight_results():
    """Verify search_one_way_flights returns empty itineraries list when no flights found."""
    service = IgnavService(api_key="test_api_key_123")
    empty_response = {
        "origin": "DEL",
        "destination": "IXG",
        "departure_date": "2026-12-01",
        "itineraries": [],
    }
    mock_resp = create_mock_http_response(empty_response)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = service.search_one_way_flights("DEL", "IXG", "2026-12-01")

        assert isinstance(result, dict)
        assert result["origin"] == "DEL"
        assert result["destination"] == "IXG"
        assert result["itineraries"] == []


def test_secret_not_exposed_in_repr():
    """Verify service __repr__ masks the API key."""
    service = IgnavService(api_key="ignav_secret_1234567890abcdef")
    repr_str = repr(service)
    assert "ignav_secret_1234567890abcdef" not in repr_str
    assert "ignav_...cdef" in repr_str


def test_get_ignav_service_singleton():
    """Verify get_ignav_service returns a singleton instance."""
    s1 = get_ignav_service()
    s2 = get_ignav_service()
    assert s1 is s2
    assert isinstance(s1, IgnavService)

