import io
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.nuitee_service import (
    NuiteeService,
    NuiteeError,
    NuiteeConfigurationError,
    NuiteeAuthenticationError,
    NuiteeNetworkError,
    NuiteeResponseError,
    get_nuitee_service,
)


SAMPLE_HOTEL_RATES_RESPONSE = {
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
        },
        {
            "hotelId": "lp4d5e6f",
            "roomTypes": [
                {
                    "offerId": "offer_def456",
                    "rates": [
                        {
                            "name": "Standard Room",
                            "boardName": "Bed and Breakfast",
                            "retailRate": {
                                "total": [
                                    {"amount": 3800.00, "currency": "INR"}
                                ]
                            },
                        }
                    ],
                }
            ],
        },
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
        },
        {
            "id": "lp4d5e6f",
            "name": "Hotel Sea Green",
            "starRating": 3,
            "main_photo": "https://photos.liteapi.travel/sea_green.jpg",
            "address": "Marine Drive, Mumbai",
            "rating": 7.5,
            "location": {"latitude": 18.9432, "longitude": 72.8235},
        },
    ],
}


SAMPLE_HOTEL_DETAILS_RESPONSE = {
    "data": {
        "id": "lp1a2b3c",
        "name": "Taj Mahal Palace",
        "hotelDescription": "An iconic luxury hotel overlooking the Gateway of India.",
        "starRating": 5,
        "address": "Apollo Bunder, Colaba, Mumbai 400001",
        "location": {"latitude": 18.9217, "longitude": 72.8332},
        "hotelImages": [
            {"url": "https://photos.liteapi.travel/taj_palace_1.jpg", "caption": "Exterior"},
            {"url": "https://photos.liteapi.travel/taj_palace_2.jpg", "caption": "Lobby"},
        ],
        "hotelFacilities": ["WiFi", "Swimming Pool", "Spa", "Restaurant"],
        "rooms": [
            {"roomId": "rm001", "name": "Deluxe Room", "maxOccupancy": 2},
            {"roomId": "rm002", "name": "Suite", "maxOccupancy": 3},
        ],
    }
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


# ──────────────────────────────────────────────────────────────────
#  Hotel Rate Search – Success Cases
# ──────────────────────────────────────────────────────────────────

def test_search_hotel_rates_success_by_city():
    """Verify successful hotel rate search by city sends correct POST payload and returns parsed data."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    mock_resp = create_mock_http_response(SAMPLE_HOTEL_RATES_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = service.search_hotel_rates(
            checkin="2026-12-20",
            checkout="2026-12-22",
            city_name="Mumbai",
            country_code="IN",
            adults=2,
            currency="INR",
            guest_nationality="IN",
        )

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        assert req.get_method() == "POST"
        assert req.get_header("X-api-key") == "test_nuitee_key_123"
        assert req.get_header("Content-type") == "application/json"
        assert "/hotels/rates" in req.full_url

        body = json.loads(req.data.decode("utf-8"))
        assert body["checkin"] == "2026-12-20"
        assert body["checkout"] == "2026-12-22"
        assert body["cityName"] == "Mumbai"
        assert body["countryCode"] == "IN"
        assert body["currency"] == "INR"
        assert body["guestNationality"] == "IN"
        assert body["occupancies"] == [{"adults": 2, "children": []}]
        assert body["includeHotelData"] is True

        assert isinstance(result, dict)
        assert len(result["data"]) == 2
        assert result["data"][0]["hotelId"] == "lp1a2b3c"
        assert len(result["hotels"]) == 2
        assert result["hotels"][0]["name"] == "Taj Mahal Palace"


def test_search_hotel_rates_by_coordinates():
    """Verify hotel rate search by latitude/longitude sends correct location fields."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    mock_resp = create_mock_http_response(SAMPLE_HOTEL_RATES_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = service.search_hotel_rates(
            checkin="2026-12-20",
            checkout="2026-12-22",
            latitude=18.9217,
            longitude=72.8332,
            radius=10,
        )

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["latitude"] == 18.9217
        assert body["longitude"] == 72.8332
        assert body["radius"] == 10
        assert "cityName" not in body
        assert isinstance(result, dict)


def test_search_hotel_rates_by_hotel_ids():
    """Verify hotel rate search by explicit hotel IDs sends hotelIds in payload."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    mock_resp = create_mock_http_response(SAMPLE_HOTEL_RATES_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = service.search_hotel_rates(
            checkin="2026-12-20",
            checkout="2026-12-22",
            hotel_ids=["lp1a2b3c", "lp4d5e6f"],
        )

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["hotelIds"] == ["lp1a2b3c", "lp4d5e6f"]
        assert isinstance(result, dict)


def test_search_hotel_rates_custom_occupancies():
    """Verify custom occupancies override the default adults-only occupancy."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    mock_resp = create_mock_http_response(SAMPLE_HOTEL_RATES_RESPONSE)

    custom_occupancies = [
        {"adults": 2, "children": [5, 8]},
        {"adults": 1, "children": []},
    ]

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        service.search_hotel_rates(
            checkin="2026-12-20",
            checkout="2026-12-22",
            city_name="Delhi",
            country_code="IN",
            occupancies=custom_occupancies,
        )

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["occupancies"] == custom_occupancies


def test_search_hotel_rates_empty_results():
    """Verify search returns empty data gracefully when no hotels match."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    empty_response = {"data": [], "hotels": []}
    mock_resp = create_mock_http_response(empty_response)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = service.search_hotel_rates(
            checkin="2026-12-20",
            checkout="2026-12-22",
            city_name="Nowhere",
            country_code="XX",
        )

        assert isinstance(result, dict)
        assert result["data"] == []
        assert result["hotels"] == []


# ──────────────────────────────────────────────────────────────────
#  Hotel Details – Success
# ──────────────────────────────────────────────────────────────────

def test_get_hotel_details_success():
    """Verify successful hotel detail retrieval sends correct GET request and returns parsed data."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    mock_resp = create_mock_http_response(SAMPLE_HOTEL_DETAILS_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = service.get_hotel_details(hotel_id="lp1a2b3c")

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert isinstance(req, urllib.request.Request)
        assert req.get_method() == "GET"
        assert req.get_header("X-api-key") == "test_nuitee_key_123"
        assert "hotelId=lp1a2b3c" in req.full_url
        assert "/data/hotel" in req.full_url

        assert isinstance(result, dict)
        assert result["data"]["name"] == "Taj Mahal Palace"
        assert result["data"]["starRating"] == 5
        assert len(result["data"]["hotelImages"]) == 2


def test_get_hotel_details_missing_hotel_id():
    """Verify empty hotel_id raises ValueError."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    with pytest.raises(ValueError, match="hotel_id is required"):
        service.get_hotel_details(hotel_id="")
    with pytest.raises(ValueError, match="hotel_id is required"):
        service.get_hotel_details(hotel_id="   ")


# ──────────────────────────────────────────────────────────────────
#  Validation Errors
# ──────────────────────────────────────────────────────────────────

def test_missing_location_filter_raises_value_error():
    """Verify that no location filter raises ValueError."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    with pytest.raises(ValueError, match="At least one location filter is required"):
        service.search_hotel_rates(
            checkin="2026-12-20",
            checkout="2026-12-22",
        )


def test_missing_dates_raises_value_error():
    """Verify missing checkin or checkout raises ValueError."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    with pytest.raises(ValueError, match="checkin and checkout dates are required"):
        service.search_hotel_rates(checkin="", checkout="2026-12-22", city_name="Mumbai", country_code="IN")
    with pytest.raises(ValueError, match="checkin and checkout dates are required"):
        service.search_hotel_rates(checkin="2026-12-20", checkout="", city_name="Mumbai", country_code="IN")


# ──────────────────────────────────────────────────────────────────
#  API Key / Authentication Errors
# ──────────────────────────────────────────────────────────────────

def test_missing_api_key_raises_configuration_error():
    """Verify that calling API without an API key raises NuiteeConfigurationError."""
    service = NuiteeService(api_key="")
    with pytest.raises(NuiteeConfigurationError, match="NUITEE_API_KEY is not configured or missing"):
        service.search_hotel_rates(
            checkin="2026-12-20", checkout="2026-12-22",
            city_name="Mumbai", country_code="IN",
        )
    with pytest.raises(NuiteeConfigurationError, match="NUITEE_API_KEY is not configured or missing"):
        service.get_hotel_details(hotel_id="lp1a2b3c")


def test_authentication_failure_http_401():
    """Verify HTTP 401 raises NuiteeAuthenticationError without exposing secrets."""
    service = NuiteeService(api_key="invalid_nuitee_key")
    error_body = json.dumps({"error": "Invalid API key"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://api.liteapi.travel/v3.0/hotels/rates",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(error_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(NuiteeAuthenticationError) as exc_info:
            service.search_hotel_rates(
                checkin="2026-12-20", checkout="2026-12-22",
                city_name="Mumbai", country_code="IN",
            )
        assert "authentication failed" in str(exc_info.value).lower()
        assert "401" in str(exc_info.value)
        assert "invalid_nuitee_key" not in str(exc_info.value)


def test_authentication_failure_http_403():
    """Verify HTTP 403 raises NuiteeAuthenticationError."""
    service = NuiteeService(api_key="forbidden_nuitee_key")
    error_body = json.dumps({"message": "Forbidden access"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://api.liteapi.travel/v3.0/data/hotel",
        code=403,
        msg="Forbidden",
        hdrs={},
        fp=io.BytesIO(error_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(NuiteeAuthenticationError) as exc_info:
            service.get_hotel_details(hotel_id="lp1a2b3c")
        assert "403" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────
#  Network Errors
# ──────────────────────────────────────────────────────────────────

def test_network_timeout_handling():
    """Verify network timeout raises NuiteeNetworkError."""
    service = NuiteeService(api_key="test_nuitee_key_123")

    # TimeoutError
    with patch("urllib.request.urlopen", side_effect=TimeoutError("The read operation timed out")):
        with pytest.raises(NuiteeNetworkError, match="timed out"):
            service.search_hotel_rates(
                checkin="2026-12-20", checkout="2026-12-22",
                city_name="Mumbai", country_code="IN",
            )

    # URLError with timeout reason
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection timed out")):
        with pytest.raises(NuiteeNetworkError, match="timed out"):
            service.get_hotel_details(hotel_id="lp1a2b3c")


def test_network_connection_failure():
    """Verify connection refused raises NuiteeNetworkError."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        with pytest.raises(NuiteeNetworkError, match="Connection refused"):
            service.search_hotel_rates(
                checkin="2026-12-20", checkout="2026-12-22",
                city_name="Mumbai", country_code="IN",
            )


# ──────────────────────────────────────────────────────────────────
#  Response Errors
# ──────────────────────────────────────────────────────────────────

def test_invalid_json_response():
    """Verify non-JSON response raises NuiteeResponseError."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    mock_resp = create_mock_http_response("<html><body>502 Bad Gateway</body></html>")

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(NuiteeResponseError, match="Invalid JSON response"):
            service.search_hotel_rates(
                checkin="2026-12-20", checkout="2026-12-22",
                city_name="Mumbai", country_code="IN",
            )

    mock_resp2 = create_mock_http_response("<html><body>Bad Gateway</body></html>")
    with patch("urllib.request.urlopen", return_value=mock_resp2):
        with pytest.raises(NuiteeResponseError, match="Invalid JSON response"):
            service.get_hotel_details(hotel_id="lp1a2b3c")


def test_http_500_server_error():
    """Verify HTTP 500 raises NuiteeResponseError."""
    service = NuiteeService(api_key="test_nuitee_key_123")
    error_body = json.dumps({"error": "Internal server error"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://api.liteapi.travel/v3.0/hotels/rates",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(error_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(NuiteeResponseError) as exc_info:
            service.search_hotel_rates(
                checkin="2026-12-20", checkout="2026-12-22",
                city_name="Mumbai", country_code="IN",
            )
        assert "500" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────
#  Repr & Singleton
# ──────────────────────────────────────────────────────────────────

def test_api_key_masking_in_repr():
    """Verify service __repr__ masks the API key."""
    service = NuiteeService(api_key="nuitee_secret_1234567890abcdef")
    repr_str = repr(service)
    assert "nuitee_secret_1234567890abcdef" not in repr_str
    assert "nuitee...cdef" in repr_str
    assert "NuiteeService" in repr_str


def test_api_key_masking_short_key():
    """Verify short API key is fully masked."""
    service = NuiteeService(api_key="short")
    repr_str = repr(service)
    assert "short" not in repr_str
    assert "***" in repr_str


def test_get_nuitee_service_singleton():
    """Verify get_nuitee_service returns a singleton instance."""
    import backend.app.services.nuitee_service as mod
    mod._nuitee_service_instance = None  # Reset for test isolation
    s1 = get_nuitee_service()
    s2 = get_nuitee_service()
    assert s1 is s2
    assert isinstance(s1, NuiteeService)
    mod._nuitee_service_instance = None  # Clean up
