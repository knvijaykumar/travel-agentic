from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.place import Place
from backend.app.api.v1.endpoints.places import (
    get_geoapify_service,
    get_wikimedia_service,
    get_clip_service,
    build_place_description,
)
from backend.app.services.clip_service import CLIPService
from backend.app.services.geoapify_service import GeoapifyService
from backend.app.services.wikimedia_service import WikimediaService


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Clear FastAPI dependency overrides after each test and mock CLIPService by default."""
    app.dependency_overrides.clear()
    mock_clip = MagicMock(spec=CLIPService)
    # Default mock returns 0.5 for any images to avoid network/model loading in fast tests
    mock_clip.compute_batch_similarity.side_effect = lambda images, text, **kwargs: [0.5] * len(images)
    app.dependency_overrides[get_clip_service] = lambda: mock_clip
    yield
    app.dependency_overrides.clear()



@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_place_search_success(client):
    """Verify successful GET /api/v1/places/search returns validated Place list."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Wax World Museum",
            category="entertainment.museum",
            latitude=15.501,
            longitude=73.912,
            address="Old Goa, Panaji, Goa",
            city="Panaji",
            country="India",
            source_provider="Geoapify",
        ),
        Place(
            place_id="geo_2",
            name="Aguada Fort",
            category="tourism.sights",
            latitude=15.492,
            longitude=73.773,
            source_provider="Geoapify",
        ),
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_image.return_value = None

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki

    response = client.get(
        "/api/v1/places/search",
        params={
            "category": "entertainment.museum",
            "latitude": 15.501,
            "longitude": 73.912,
            "radius_meters": 5000,
            "limit": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "Wax World Museum"
    assert data[0]["place_id"] == "geo_1"
    assert data[0]["latitude"] == 15.501
    assert data[0]["source_provider"] == "Geoapify"
    assert data[1]["name"] == "Aguada Fort"


def test_place_search_with_wikimedia_enrichment_success(client):
    """Verify Wikimedia image and attribution are correctly attached to corresponding Place."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Wax World Museum",
            category="entertainment.museum",
            latitude=15.501,
            longitude=73.912,
            source_provider="Geoapify",
        ),
        Place(
            place_id="geo_2",
            name="Aguada Fort",
            category="tourism.sights",
            latitude=15.492,
            longitude=73.773,
            source_provider="Geoapify",
        ),
    ]

    def mock_get_image(place_name: str, *args, **kwargs):
        if place_name == "Wax World Museum":
            return {
                "image_url": "https://upload.wikimedia.org/wax.jpg",
                "attribution": "Photographer A (CC-BY 4.0)",
            }
        elif place_name == "Aguada Fort":
            return {
                "image_url": "https://upload.wikimedia.org/fort.jpg",
                "attribution": "Photographer B (CC0)",
            }
        return None

    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_image.side_effect = mock_get_image

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki

    response = client.get(
        "/api/v1/places/search",
        params={"category": "entertainment.museum", "latitude": 15.5, "longitude": 73.8},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Check Place 1 enrichment
    assert data[0]["name"] == "Wax World Museum"
    assert data[0]["image_url"] == "https://upload.wikimedia.org/wax.jpg"
    assert data[0]["image_attribution"] == "Photographer A (CC-BY 4.0)"

    # Check Place 2 enrichment
    assert data[1]["name"] == "Aguada Fort"
    assert data[1]["image_url"] == "https://upload.wikimedia.org/fort.jpg"
    assert data[1]["image_attribution"] == "Photographer B (CC0)"


def test_place_search_with_wikimedia_missing_image(client):
    """Verify places retain null image fields when Wikimedia returns None."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Unknown Spot",
            category="tourism.sights",
            latitude=15.501,
            longitude=73.912,
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_image.return_value = None

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki

    response = client.get(
        "/api/v1/places/search",
        params={"category": "tourism.sights", "latitude": 15.5, "longitude": 73.8},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Unknown Spot"
    assert data[0]["image_url"] is None
    assert data[0]["image_attribution"] is None


def test_place_search_with_wikimedia_failure_gracefully_degrades(client):
    """Verify Wikimedia errors/exceptions do not fail the request; places returned with null image fields."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Aguada Fort",
            category="tourism.sights",
            latitude=15.492,
            longitude=73.773,
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_image.side_effect = RuntimeError("Wikimedia 503 Service Unavailable")

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki

    response = client.get(
        "/api/v1/places/search",
        params={"category": "tourism.sights", "latitude": 15.5, "longitude": 73.8},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Aguada Fort"
    assert data[0]["image_url"] is None
    assert data[0]["image_attribution"] is None


def test_place_search_defaults(client):
    """Verify default radius (5000) and limit (20) are passed to service."""
    mock_service = MagicMock(spec=GeoapifyService)
    mock_service.search_places.return_value = []
    app.dependency_overrides[get_geoapify_service] = lambda: mock_service

    response = client.get(
        "/api/v1/places/search",
        params={
            "category": "tourism",
            "latitude": 15.0,
            "longitude": 73.0,
        },
    )

    assert response.status_code == 200
    mock_service.search_places.assert_called_once_with(
        category="tourism",
        latitude=15.0,
        longitude=73.0,
        radius_meters=5000,
        limit=20,
    )


def test_place_search_empty_results(client):
    """Verify empty result returns an empty JSON list."""
    mock_service = MagicMock(spec=GeoapifyService)
    mock_service.search_places.return_value = []
    app.dependency_overrides[get_geoapify_service] = lambda: mock_service

    response = client.get(
        "/api/v1/places/search",
        params={"category": "museum", "latitude": 15.0, "longitude": 73.0},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "invalid_params",
    [
        {"latitude": 15.0, "longitude": 73.0},  # missing category
        {"category": "museum", "longitude": 73.0},  # missing latitude
        {"category": "museum", "latitude": 15.0},  # missing longitude
        {"category": "museum", "latitude": 95.0, "longitude": 73.0},  # lat > 90
        {"category": "museum", "latitude": -95.0, "longitude": 73.0},  # lat < -90
        {"category": "museum", "latitude": 15.0, "longitude": 185.0},  # lon > 180
        {"category": "museum", "latitude": 15.0, "longitude": -185.0},  # lon < -180
        {"category": "museum", "latitude": 15.0, "longitude": 73.0, "limit": 25},  # limit > 20
        {"category": "museum", "latitude": 15.0, "longitude": 73.0, "limit": 0},  # limit <= 0
        {"category": "museum", "latitude": 15.0, "longitude": 73.0, "radius_meters": 0},  # radius <= 0
        {"category": "   ", "latitude": 15.0, "longitude": 73.0},  # blank category
    ],
)
def test_place_search_invalid_parameters(client, invalid_params):
    """Verify invalid query parameter bounds return 422 Unprocessable Entity."""
    response = client.get("/api/v1/places/search", params=invalid_params)
    assert response.status_code == 422


def test_place_search_provider_error(client):
    """Verify service exceptions are handled with HTTP 502 Bad Gateway."""
    mock_service = MagicMock(spec=GeoapifyService)
    mock_service.search_places.side_effect = RuntimeError("Upstream Geoapify connection failed")
    app.dependency_overrides[get_geoapify_service] = lambda: mock_service

    response = client.get(
        "/api/v1/places/search",
        params={"category": "museum", "latitude": 15.0, "longitude": 73.0},
    )

    assert response.status_code == 502
    assert "Provider error" in response.json()["detail"]


def test_place_search_forwards_city_and_region_to_wikimedia(client):
    """Verify that enrich_places_with_images passes place name, city, and region to get_image."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Wax World Museum",
            category="entertainment.museum",
            latitude=15.501,
            longitude=73.912,
            address="Old Goa, Panaji, Goa",
            city="Panaji",
            country="India",
            source_provider="Geoapify",
        ),
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_image.return_value = {
        "image_url": "https://upload.wikimedia.org/wax.jpg",
        "attribution": "Photographer",
    }

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki

    response = client.get(
        "/api/v1/places/search",
        params={"category": "entertainment.museum", "latitude": 15.501, "longitude": 73.912},
    )

    assert response.status_code == 200
    mock_wiki.get_image.assert_called_once_with(
        place_name="Wax World Museum",
        city="Panaji",
        region="Goa",
    )


def test_build_place_description():
    """Verify natural descriptive prompt construction for CLIP."""
    place1 = Place(
        place_id="1",
        name="Gateway of India",
        category="tourism.sights",
        latitude=18.922,
        longitude=72.834,
        country="India",
        source_provider="Geoapify",
    )
    desc1 = build_place_description(place1, city="Mumbai", region="Maharashtra")
    assert "Gateway of India" in desc1
    assert "tourism sights" in desc1
    assert "Mumbai" in desc1
    assert "Maharashtra" in desc1
    assert "India" in desc1

    place2 = Place(
        place_id="2",
        name="Mysuru Rail Museum",
        category="museum",
        latitude=12.316,
        longitude=76.644,
        source_provider="Geoapify",
    )
    desc2 = build_place_description(place2, city="Mysuru")
    assert desc2 == "A photo of Mysuru Rail Museum, a museum in Mysuru"


def test_place_search_with_clip_ranking_selects_highest_scoring_candidate(client):
    """Verify CLIP similarity scores rank candidates and select the highest scoring image."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_fort",
            name="Aguada Fort",
            category="tourism.sights",
            latitude=15.492,
            longitude=73.773,
            city="Candolim",
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_candidates.return_value = [
        {
            "title": "File:Aguada Fort Map.jpg",
            "image_url": "https://upload.wikimedia.org/map.jpg",
            "attribution": "Cartographer (CC-BY 3.0)",
        },
        {
            "title": "File:Aguada Fort Panorama.jpg",
            "image_url": "https://upload.wikimedia.org/panorama.jpg",
            "attribution": "Photographer P (CC-BY-SA 4.0)",
        },
        {
            "title": "File:Aguada Fort Ticket Counter.jpg",
            "image_url": "https://upload.wikimedia.org/ticket.jpg",
            "attribution": "Visitor V (CC0)",
        },
    ]

    mock_clip = MagicMock(spec=CLIPService)
    # Cand 2 scores highest (0.38) vs Cand 1 (0.15) and Cand 3 (0.22)
    mock_clip.compute_batch_similarity.return_value = [0.15, 0.38, 0.22]

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki
    app.dependency_overrides[get_clip_service] = lambda: mock_clip

    response = client.get(
        "/api/v1/places/search",
        params={"category": "tourism.sights", "latitude": 15.492, "longitude": 73.773},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    # Cand 2 selected based on highest similarity score
    assert data[0]["image_url"] == "https://upload.wikimedia.org/panorama.jpg"
    assert data[0]["image_attribution"] == "Photographer P (CC-BY-SA 4.0)"
    mock_clip.compute_batch_similarity.assert_called_once()


def test_place_search_wrong_location_rejected_before_clip():
    """Verify candidate from conflicting location is filtered out by Wikimedia service before CLIP."""
    from unittest.mock import patch
    service = WikimediaService()

    # Query Commons returning one candidate for Mysore and one candidate for Goa
    mock_data = {
        "query": {
            "pages": {
                "1": {
                    "index": 1,
                    "title": "File:Melody World Wax Museum Mysore.jpg",
                    "imageinfo": [{"url": "https://upload.wikimedia.org/wax_mysore.jpg", "mime": "image/jpeg"}],
                },
                "2": {
                    "index": 2,
                    "title": "File:Wax World Museum Old Goa.jpg",
                    "imageinfo": [{"url": "https://upload.wikimedia.org/wax_goa.jpg", "mime": "image/jpeg"}],
                },
            }
        }
    }

    with patch.object(service, "_query_commons", return_value=mock_data):
        candidates = service.get_candidates("Wax World Museum", city="Panaji", region="Goa", limit=3)
        # Mysore image should be discarded by hard metadata location check
        assert len(candidates) == 1
        assert candidates[0]["image_url"] == "https://upload.wikimedia.org/wax_goa.jpg"


def test_place_search_clip_handles_invalid_candidate_images(client):
    """Verify invalid candidate images (None score) are discarded; valid or null returned."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Place One",
            category="museum",
            latitude=15.0,
            longitude=73.0,
            source_provider="Geoapify",
        ),
        Place(
            place_id="geo_2",
            name="Place Two",
            category="museum",
            latitude=15.0,
            longitude=73.0,
            source_provider="Geoapify",
        ),
    ]

    def mock_get_candidates(place_name: str, *args, **kwargs):
        if place_name == "Place One":
            return [
                {"title": "File:broken.jpg", "image_url": "https://upload.wikimedia.org/broken.jpg", "attribution": "A"},
                {"title": "File:good.jpg", "image_url": "https://upload.wikimedia.org/good.jpg", "attribution": "B"},
            ]
        elif place_name == "Place Two":
            return [
                {"title": "File:corrupt1.jpg", "image_url": "https://upload.wikimedia.org/corrupt1.jpg", "attribution": "C"},
                {"title": "File:corrupt2.jpg", "image_url": "https://upload.wikimedia.org/corrupt2.jpg", "attribution": "D"},
            ]
        return []

    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_candidates.side_effect = mock_get_candidates

    mock_clip = MagicMock(spec=CLIPService)

    def mock_similarity(images, text, **kwargs):
        if "https://upload.wikimedia.org/good.jpg" in images:
            # First is None (broken), second is 0.31 (valid)
            return [None, 0.31]
        elif "https://upload.wikimedia.org/corrupt1.jpg" in images:
            # Both corrupt
            return [None, None]
        return [0.5] * len(images)

    mock_clip.compute_batch_similarity.side_effect = mock_similarity

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki
    app.dependency_overrides[get_clip_service] = lambda: mock_clip

    response = client.get(
        "/api/v1/places/search",
        params={"category": "museum", "latitude": 15.0, "longitude": 73.0},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Place One: invalid image discarded, valid image selected
    assert data[0]["name"] == "Place One"
    assert data[0]["image_url"] == "https://upload.wikimedia.org/good.jpg"
    assert data[0]["image_attribution"] == "B"

    # Place Two: all images invalid, returns safe null
    assert data[1]["name"] == "Place Two"
    assert data[1]["image_url"] is None
    assert data[1]["image_attribution"] is None


def test_place_search_clip_model_unavailable_falls_back_gracefully(client):
    """Verify that when CLIP service is None or inference raises an exception, API degrades gracefully."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Aguada Fort",
            category="sights",
            latitude=15.0,
            longitude=73.0,
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_candidates.return_value = [
        {"title": "File:cand1.jpg", "image_url": "https://upload.wikimedia.org/cand1.jpg", "attribution": "Attr 1"},
        {"title": "File:cand2.jpg", "image_url": "https://upload.wikimedia.org/cand2.jpg", "attribution": "Attr 2"},
    ]

    # Subcase A: clip_service dependency returns None
    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki
    app.dependency_overrides[get_clip_service] = lambda: None

    response = client.get(
        "/api/v1/places/search",
        params={"category": "sights", "latitude": 15.0, "longitude": 73.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data[0]["image_url"] == "https://upload.wikimedia.org/cand1.jpg"
    assert data[0]["image_attribution"] == "Attr 1"

    # Subcase B: clip_service raises runtime inference exception
    mock_clip = MagicMock(spec=CLIPService)
    mock_clip.compute_batch_similarity.side_effect = RuntimeError("PyTorch CUDA out of memory")
    app.dependency_overrides[get_clip_service] = lambda: mock_clip

    response_b = client.get(
        "/api/v1/places/search",
        params={"category": "sights", "latitude": 15.0, "longitude": 73.0},
    )
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert data_b[0]["image_url"] == "https://upload.wikimedia.org/cand1.jpg"
    assert data_b[0]["image_attribution"] == "Attr 1"


def test_place_search_no_suitable_candidates_returns_null(client):
    """Verify places return null image_url and image_attribution when no candidates exist."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Rare Hidden Temple",
            category="tourism.sights",
            latitude=15.0,
            longitude=73.0,
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_candidates.return_value = []

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki

    response = client.get(
        "/api/v1/places/search",
        params={"category": "tourism.sights", "latitude": 15.0, "longitude": 73.0},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["image_url"] is None
    assert data[0]["image_attribution"] is None


def test_place_search_preserves_image_attribution(client):
    """Verify selected candidate's full attribution string is preserved intact."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_1",
            name="Mysuru Palace",
            category="tourism.sights",
            latitude=12.305,
            longitude=76.655,
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_candidates.return_value = [
        {
            "title": "File:Mysore Palace Illumination.jpg",
            "image_url": "https://upload.wikimedia.org/illumination.jpg",
            "attribution": "© Muhammad Mahdi Karim (CC-BY-SA 3.0 GFDL)",
        }
    ]

    mock_clip = MagicMock(spec=CLIPService)
    mock_clip.compute_batch_similarity.return_value = [0.42]

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki
    app.dependency_overrides[get_clip_service] = lambda: mock_clip

    response = client.get(
        "/api/v1/places/search",
        params={"category": "tourism.sights", "latitude": 12.305, "longitude": 76.655},
    )

    assert response.status_code == 200
    data = response.json()
    assert data[0]["image_attribution"] == "© Muhammad Mahdi Karim (CC-BY-SA 3.0 GFDL)"


def test_place_search_api_response_schema_compatibility(client):
    """Verify that Places API response adheres strictly to Place schema specification."""
    mock_geo = MagicMock(spec=GeoapifyService)
    mock_geo.search_places.return_value = [
        Place(
            place_id="geo_100",
            name="Gateway of India",
            category="tourism.sights",
            latitude=18.922,
            longitude=72.834,
            address="Apollo Bandar, Colaba, Mumbai, Maharashtra 400001",
            city="Mumbai",
            country="India",
            source_provider="Geoapify",
        )
    ]
    mock_wiki = MagicMock(spec=WikimediaService)
    mock_wiki.get_candidates.return_value = [
        {
            "title": "File:Gateway of India Mumbai.jpg",
            "image_url": "https://upload.wikimedia.org/gateway.jpg",
            "attribution": "Photographer (CC-BY-SA 4.0)",
        }
    ]
    mock_clip = MagicMock(spec=CLIPService)
    mock_clip.compute_batch_similarity.return_value = [0.35]

    app.dependency_overrides[get_geoapify_service] = lambda: mock_geo
    app.dependency_overrides[get_wikimedia_service] = lambda: mock_wiki
    app.dependency_overrides[get_clip_service] = lambda: mock_clip

    response = client.get(
        "/api/v1/places/search",
        params={"category": "tourism.sights", "latitude": 18.922, "longitude": 72.834},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]

    # Validate against Pydantic schema
    validated_place = Place(**item)
    assert validated_place.place_id == "geo_100"
    assert validated_place.name == "Gateway of India"
    assert validated_place.category == "tourism.sights"
    assert validated_place.latitude == 18.922
    assert validated_place.longitude == 72.834
    assert validated_place.city == "Mumbai"
    assert validated_place.image_url == "https://upload.wikimedia.org/gateway.jpg"
    assert validated_place.image_attribution == "Photographer (CC-BY-SA 4.0)"
    assert validated_place.source_provider == "Geoapify"

