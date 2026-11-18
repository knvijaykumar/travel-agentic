import json
import io
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from backend.app.services.geoapify_service import GeoapifyService
from backend.app.schemas.place import Place


SAMPLE_GEOJSON_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Wax World Museum",
                "categories": ["entertainment.museum"],
                "lat": 15.501,
                "lon": 73.912,
                "formatted": "Old Goa, Panaji - 403108, Goa, India",
                "city": "Panaji",
                "country": "India",
                "place_id": "place_wax_123",
            },
            "geometry": {"type": "Point", "coordinates": [73.912, 15.501]},
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Aguada Fort",
                "categories": ["tourism.sights"],
                "lat": 15.492,
                "lon": 73.773,
                "formatted": "Sinquerim, Goa, India",
                "city": "Sinquerim",
                "country": "India",
                "place_id": "place_fort_456",
            },
            "geometry": {"type": "Point", "coordinates": [73.773, 15.492]},
        },
    ],
}


def create_mock_http_response(data: dict, status_code: int = 200):
    """Helper to mock urllib.request.urlopen response context manager."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = status_code
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp


def test_search_places_success():
    """Verify places are successfully parsed and validated from Geoapify response."""
    service = GeoapifyService(api_key="mock_key_test")
    mock_resp = create_mock_http_response(SAMPLE_GEOJSON_RESPONSE)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        places = service.search_places(
            category="entertainment.museum",
            latitude=15.501,
            longitude=73.912,
            radius_meters=5000,
        )

        assert mock_urlopen.called
        assert len(places) == 2
        p1, p2 = places

        assert isinstance(p1, Place)
        assert p1.place_id == "place_wax_123"
        assert p1.name == "Wax World Museum"
        assert p1.latitude == 15.501
        assert p1.longitude == 73.912
        assert p1.city == "Panaji"
        assert p1.country == "India"
        assert p1.source_provider == "Geoapify"

        assert isinstance(p2, Place)
        assert p2.name == "Aguada Fort"


def test_search_places_empty_results():
    """Verify empty features array returns an empty list."""
    service = GeoapifyService(api_key="mock_key_test")
    mock_resp = create_mock_http_response({"features": []})

    with patch("urllib.request.urlopen", return_value=mock_resp):
        places = service.search_places("entertainment.museum", 15.0, 73.0)
        assert places == []


def test_search_places_missing_name_fallback():
    """Verify feature with missing name uses address_line1 or fallback string."""
    service = GeoapifyService(api_key="mock_key_test")
    feature_no_name = {
        "features": [
            {
                "properties": {
                    "name": None,
                    "address_line1": "Historic Tower",
                    "lat": 15.4,
                    "lon": 73.8,
                    "place_id": "tower_1",
                }
            }
        ]
    }
    mock_resp = create_mock_http_response(feature_no_name)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        places = service.search_places("tourism.sights", 15.4, 73.8)
        assert len(places) == 1
        assert places[0].name == "Historic Tower"


def test_search_places_missing_or_invalid_coordinates_skipped():
    """Verify features without valid coordinates are safely skipped."""
    service = GeoapifyService(api_key="mock_key_test")
    bad_features = {
        "features": [
            {
                "properties": {"name": "No Coords", "lat": None, "lon": None},
                "geometry": {},
            },
            {
                "properties": {"name": "Out of bounds", "lat": 120.0, "lon": 73.0},
            },
            {
                "properties": {"name": "Valid Place", "lat": 15.5, "lon": 73.8, "place_id": "val_1"},
            },
        ]
    }
    mock_resp = create_mock_http_response(bad_features)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        places = service.search_places("tourism", 15.5, 73.8)
        assert len(places) == 1
        assert places[0].name == "Valid Place"


def test_search_places_missing_address_optional():
    """Verify missing address properties default cleanly to None."""
    service = GeoapifyService(api_key="mock_key_test")
    feature_no_addr = {
        "features": [
            {
                "properties": {
                    "name": "Beach Point",
                    "lat": 15.5,
                    "lon": 73.8,
                    "place_id": "beach_1",
                }
            }
        ]
    }
    mock_resp = create_mock_http_response(feature_no_addr)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        places = service.search_places("beach", 15.5, 73.8)
        assert len(places) == 1
        assert places[0].address is None
        assert places[0].city is None


def test_search_places_http_error():
    """Verify HTTP errors (e.g., 401 Unauthorized, 403 Forbidden) are caught safely."""
    service = GeoapifyService(api_key="mock_key_test")
    http_err = urllib.error.HTTPError(
        url="https://api.geoapify.com",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b'{"message": "Invalid API key"}'),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        places = service.search_places("museum", 15.0, 73.0)
        assert places == []


def test_search_places_timeout_error():
    """Verify request timeout is caught safely without raising."""
    service = GeoapifyService(api_key="mock_key_test")

    with patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
        places = service.search_places("museum", 15.0, 73.0)
        assert places == []


def test_search_places_missing_api_key():
    """Verify empty API key returns immediately without making network calls."""
    service = GeoapifyService(api_key="")

    with patch("urllib.request.urlopen") as mock_urlopen:
        places = service.search_places("museum", 15.0, 73.0)
        assert places == []
        assert not mock_urlopen.called


def test_search_places_invalid_input_coordinates():
    """Verify invalid input coordinates abort before calling network."""
    service = GeoapifyService(api_key="mock_key_test")

    with patch("urllib.request.urlopen") as mock_urlopen:
        places = service.search_places("museum", latitude=100.0, longitude=73.0)
        assert places == []
        assert not mock_urlopen.called

