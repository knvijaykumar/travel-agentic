import pytest
from pydantic import ValidationError

from backend.app.schemas.place import Place


def test_valid_place_minimal():
    """Verify that a Place can be instantiated with only required fields."""
    place = Place(
        place_id="geo_123",
        name="Aguada Fort",
        category="tourism.sights",
        latitude=15.492,
        longitude=73.773,
        source_provider="Geoapify",
    )
    assert place.place_id == "geo_123"
    assert place.name == "Aguada Fort"
    assert place.latitude == 15.492
    assert place.longitude == 73.773
    assert place.source_provider == "Geoapify"
    assert place.address is None
    assert place.image_url is None


def test_valid_place_full():
    """Verify that a Place can be instantiated with all optional fields."""
    place = Place(
        place_id="geo_456",
        name="Wax World Museum",
        category="entertainment.museum",
        latitude=15.501,
        longitude=73.912,
        address="Old Goa, Panaji - 403108, Goa, India",
        city="Panaji",
        country="India",
        image_url="https://example.com/museum.jpg",
        image_attribution="CC-BY-SA 4.0",
        source_provider="Geoapify",
    )
    assert place.city == "Panaji"
    assert place.country == "India"
    assert place.image_url == "https://example.com/museum.jpg"
    assert place.image_attribution == "CC-BY-SA 4.0"


@pytest.mark.parametrize("invalid_lat", [-90.1, 90.1, 120.0, -100.0])
def test_invalid_latitude(invalid_lat):
    """Verify latitude boundary constraints [-90, 90]."""
    with pytest.raises(ValidationError) as exc_info:
        Place(
            place_id="geo_1",
            name="Test Place",
            category="sight",
            latitude=invalid_lat,
            longitude=73.0,
            source_provider="Geoapify",
        )
    assert "latitude" in str(exc_info.value)


@pytest.mark.parametrize("invalid_lon", [-180.1, 180.1, 200.0, -195.0])
def test_invalid_longitude(invalid_lon):
    """Verify longitude boundary constraints [-180, 180]."""
    with pytest.raises(ValidationError) as exc_info:
        Place(
            place_id="geo_1",
            name="Test Place",
            category="sight",
            latitude=15.0,
            longitude=invalid_lon,
            source_provider="Geoapify",
        )
    assert "longitude" in str(exc_info.value)


@pytest.mark.parametrize("bad_name", ["", "   "])
def test_empty_or_whitespace_name(bad_name):
    """Verify that empty or whitespace-only name is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Place(
            place_id="geo_1",
            name=bad_name,
            category="sight",
            latitude=15.0,
            longitude=73.0,
            source_provider="Geoapify",
        )
    assert "name" in str(exc_info.value)


@pytest.mark.parametrize("bad_provider", ["", "   "])
def test_empty_or_whitespace_provider(bad_provider):
    """Verify that empty or whitespace-only source_provider is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Place(
            place_id="geo_1",
            name="Valid Name",
            category="sight",
            latitude=15.0,
            longitude=73.0,
            source_provider=bad_provider,
        )
    assert "source_provider" in str(exc_info.value)

