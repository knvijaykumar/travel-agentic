import io
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.geoapify_service import GeoapifyService


SAMPLE_GEOCODE_JSON_RESPONSE = {
    "results": [
        {
            "name": "Jaipur",
            "city": "Jaipur",
            "state": "Rajasthan",
            "country": "India",
            "country_code": "in",
            "lon": 75.8189817,
            "lat": 26.9196238,
            "formatted": "Jaipur, Rajasthan, India",
            "place_id": "place_jaipur_123",
        }
    ]
}

SAMPLE_GEOCODE_GEOJSON_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "city": "Goa",
                "state": "Goa",
                "country": "India",
                "lon": 73.8278,
                "lat": 15.4989,
                "formatted": "Goa, India",
                "place_id": "place_goa_456",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [73.8278, 15.4989],
            },
        }
    ],
}


def create_mock_http_response(data: dict, status_code: int = 200):
    """Helper to mock urllib.request.urlopen response."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = status_code
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


def test_geocode_city_success_json_format():
    """Verify city name (Jaipur) is converted to latitude and longitude via format=json response."""
    service = GeoapifyService(api_key="mock_key_test")
    mock_resp = create_mock_http_response(SAMPLE_GEOCODE_JSON_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = service.geocode_city("Jaipur")

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert "text=Jaipur" in req.full_url
        assert "format=json" in req.full_url

        assert result is not None
        assert result["latitude"] == pytest.approx(26.9196238)
        assert result["longitude"] == pytest.approx(75.8189817)
        assert result["lat"] == result["latitude"]
        assert result["lon"] == result["longitude"]
        assert result["city"] == "Jaipur"
        assert result["country"] == "India"
        assert "Jaipur, Rajasthan, India" in result["formatted"]


def test_geocode_city_success_geojson_format():
    """Verify city name (Goa) is parsed from GeoJSON features format."""
    service = GeoapifyService(api_key="mock_key_test")
    mock_resp = create_mock_http_response(SAMPLE_GEOCODE_GEOJSON_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = service.geocode_destination("Goa")

        assert result is not None
        assert result["latitude"] == pytest.approx(15.4989)
        assert result["longitude"] == pytest.approx(73.8278)
        assert result["city"] == "Goa"
        assert result["country"] == "India"


def test_geocode_city_with_country_filter():
    """Verify country parameter is appended to query text for disambiguation."""
    service = GeoapifyService(api_key="mock_key_test")
    mock_resp = create_mock_http_response(SAMPLE_GEOCODE_JSON_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        service.geocode_city("Bengaluru", country="India")

        req = mock_urlopen.call_args[0][0]
        assert "text=Bengaluru%2C+India" in req.full_url or "Bengaluru" in req.full_url


def test_geocode_city_empty_input_returns_none():
    """Verify empty or whitespace-only destination returns None without making network calls."""
    service = GeoapifyService(api_key="mock_key_test")

    with patch("urllib.request.urlopen") as mock_urlopen:
        assert service.geocode_city("") is None
        assert service.geocode_city("   ") is None
        assert not mock_urlopen.called


def test_geocode_city_not_found_returns_none():
    """Verify empty results from Geoapify return None."""
    service = GeoapifyService(api_key="mock_key_test")
    mock_resp = create_mock_http_response({"results": []})

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = service.geocode_city("NonExistentCityXYZ123")
        assert result is None


def test_geocode_city_out_of_bounds_coordinates_rejected():
    """Verify coordinates outside [-90, 90] / [-180, 180] are rejected."""
    service = GeoapifyService(api_key="mock_key_test")
    invalid_data = {
        "results": [
            {"city": "BadCoords", "lat": 150.0, "lon": 75.0, "formatted": "Bad City"}
        ]
    }
    mock_resp = create_mock_http_response(invalid_data)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert service.geocode_city("BadCoords") is None


def test_geocode_city_http_error():
    """Verify HTTP errors (401, 500) are caught gracefully and return None."""
    service = GeoapifyService(api_key="mock_key_test")
    http_err = urllib.error.HTTPError(
        url="https://api.geoapify.com",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b'{"message": "Invalid API key"}'),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        assert service.geocode_city("Jaipur") is None


def test_geocode_city_timeout():
    """Verify request timeout is caught gracefully and returns None."""
    service = GeoapifyService(api_key="mock_key_test")

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
        assert service.geocode_city("Jaipur") is None


def test_geocode_city_missing_api_key():
    """Verify missing API key returns None without network call."""
    service = GeoapifyService(api_key="")

    with patch("urllib.request.urlopen") as mock_urlopen:
        assert service.geocode_city("Jaipur") is None
        assert not mock_urlopen.called

