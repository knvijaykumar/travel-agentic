import pytest
from unittest.mock import MagicMock

from backend.app.schemas.place import Place
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import DurationMatrixResponse
from backend.app.schemas.trip_aggregation import (
    TripAggregationRequest,
    TripAggregationResult,
    AggregatedHotelOption,
    HotelRoomOffer,
)
from backend.app.services.geoapify_service import GeoapifyService
from backend.app.services.ignav_service import (
    IgnavService,
    IgnavNetworkError,
)
from backend.app.services.nuitee_service import (
    NuiteeService,
    NuiteeResponseError,
)
from backend.app.services.routing_service import RoutingService
from backend.app.services.trip_aggregator_service import (
    TripAggregatorService,
    get_trip_aggregator_service,
    _deduplicate_places,
    _sanitize_error,
)


# ──────────────────────────────────────────────────────────────────
#  Mock Data Fixtures
# ──────────────────────────────────────────────────────────────────

MOCK_GEOCODE_GOA = {
    "latitude": 15.4989,
    "longitude": 73.8278,
    "city": "Goa",
    "country": "India",
    "formatted": "Goa, India",
}

MOCK_AIRPORTS_DELHI = [
    {"iata": "DEL", "name": "Indira Gandhi International Airport", "city": "Delhi", "country": "India"}
]

MOCK_AIRPORTS_GOA = [
    {"iata": "GOI", "name": "Dabolim Airport", "city": "Goa", "country": "India"},
    {"iata": "GOX", "name": "Manohar International Airport", "city": "Mopa, Goa", "country": "India"},
]

MOCK_FLIGHT_RESPONSE_DEL_GOI = {
    "origin": "DEL",
    "destination": "GOI",
    "departure_date": "2026-12-15",
    "itineraries": [
        {
            "price": {"amount": 4200.0, "currency": "INR"},
            "outbound": {
                "carrier": "IndiGo",
                "duration_minutes": 150,
                "segments": [
                    {
                        "marketing_carrier_code": "6E",
                        "flight_number": "6E-205",
                        "departure_airport": "DEL",
                        "arrival_airport": "GOI",
                        "departure_time_local": "2026-12-15T08:00:00",
                        "arrival_time_local": "2026-12-15T10:30:00",
                    }
                ],
            },
            "cabin_class": "economy",
            "ignav_id": "ignav_del_goi_1",
        }
    ],
}

MOCK_FLIGHT_RESPONSE_GOI_DEL = {
    "origin": "GOI",
    "destination": "DEL",
    "departure_date": "2026-12-17",
    "itineraries": [
        {
            "price": {"amount": 4600.0, "currency": "INR"},
            "outbound": {
                "carrier": "IndiGo",
                "duration_minutes": 155,
                "segments": [
                    {
                        "marketing_carrier_code": "6E",
                        "flight_number": "6E-206",
                        "departure_airport": "GOI",
                        "arrival_airport": "DEL",
                        "departure_time_local": "2026-12-17T18:00:00",
                        "arrival_time_local": "2026-12-17T20:35:00",
                    }
                ],
            },
            "cabin_class": "economy",
            "ignav_id": "ignav_goi_del_1",
        }
    ],
}

MOCK_HOTEL_RESPONSE = {
    "data": [
        {
            "hotelId": "lp_hotel_1",
            "roomTypes": [
                {
                    "offerId": "offer_standard_1",
                    "name": "Standard Room",
                    "rates": [
                        {
                            "name": "Standard Room",
                            "boardName": "Room Only",
                            "retailRate": {
                                "total": [{"amount": 6000.0, "currency": "INR"}],
                                "taxesAndFees": {"vat": 500.0},
                            },
                            "cancellationPolicies": {"refundableTag": "Non-Refundable"},
                        }
                    ],
                },
                {
                    "offerId": "offer_deluxe_1",
                    "name": "Deluxe Sea View",
                    "rates": [
                        {
                            "name": "Deluxe Sea View",
                            "boardName": "Bed and Breakfast",
                            "retailRate": {
                                "total": [{"amount": 9000.0, "currency": "INR"}],
                            },
                            "cancellationPolicies": {"refundableTag": "Free cancellation until Dec 10"},
                        }
                    ],
                },
            ],
        }
    ],
    "hotels": [
        {
            "id": "lp_hotel_1",
            "name": "Taj Fort Aguada Resort",
            "starRating": 5,
            "rating": 9.1,
            "address": "Sinquerim, Candolim, Goa",
            "location": {"latitude": 15.4925, "longitude": 73.7736},
            "main_photo": "https://photos.liteapi.travel/taj_fort.jpg",
        }
    ],
}

MOCK_PLACES = [
    Place(
        place_id="geo_place_1",
        name="Fort Aguada",
        category="tourism.sights.fort",
        latitude=15.4925,
        longitude=73.7736,
        address="Sinquerim, Goa",
        city="Candolim",
        country="India",
        source_provider="Geoapify",
    ),
    Place(
        place_id="geo_place_2",
        name="Basilica of Bom Jesus",
        category="heritage",
        latitude=15.5009,
        longitude=73.9116,
        address="Old Goa, Goa",
        city="Panaji",
        country="India",
        source_provider="Geoapify",
    ),
]

MOCK_DURATION_MATRIX = DurationMatrixResponse(
    durations_seconds=[[0.0, 1800.0], [1800.0, 0.0]],
    distances_meters=[[0.0, 18500.0], [18500.0, 0.0]],
    sources=[GeoCoordinates(lat=15.4925, lon=73.7736), GeoCoordinates(lat=15.5009, lon=73.9116)],
    destinations=[GeoCoordinates(lat=15.4925, lon=73.7736), GeoCoordinates(lat=15.5009, lon=73.9116)],
    is_estimated=False,
    routing_provider="osrm",
)


def create_mock_services():
    """Create configured mock services for testing aggregator."""
    mock_ignav = MagicMock(spec=IgnavService)
    mock_ignav.search_airports.side_effect = lambda query, limit=5: (
        MOCK_AIRPORTS_DELHI if "del" in query.lower() else MOCK_AIRPORTS_GOA
    )
    mock_ignav.search_one_way_flights.side_effect = lambda origin, destination, departure_date, **kwargs: (
        MOCK_FLIGHT_RESPONSE_DEL_GOI if origin == "DEL" else MOCK_FLIGHT_RESPONSE_GOI_DEL
    )

    mock_nuitee = MagicMock(spec=NuiteeService)
    mock_nuitee._api_key = "sand_test_key_123"
    mock_nuitee.search_hotel_rates.return_value = MOCK_HOTEL_RESPONSE

    mock_geoapify = MagicMock(spec=GeoapifyService)
    mock_geoapify.geocode_city.return_value = MOCK_GEOCODE_GOA
    mock_geoapify.search_places.return_value = MOCK_PLACES

    mock_routing = MagicMock(spec=RoutingService)
    mock_routing.get_distance_matrix.return_value = MOCK_DURATION_MATRIX

    return mock_ignav, mock_nuitee, mock_geoapify, mock_routing


# ──────────────────────────────────────────────────────────────────
#  Test Cases
# ──────────────────────────────────────────────────────────────────

def test_trip_aggregation_success_full():
    """Verify end-to-end trip aggregation collects flights, hotels, places, and routing."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        adults=2,
        children=[5],
        budget=50000.0,
        currency="INR",
        interests=["beach", "heritage"],
    )

    result = aggregator.aggregate_trip(req)

    assert isinstance(result, TripAggregationResult)
    assert result.destination == "Goa"
    assert result.duration_days == 3
    assert result.is_same_day is False
    assert result.destination_coordinates is not None
    assert result.destination_coordinates.lat == 15.4989

    # Multiple airport candidates preserved
    assert len(result.destination_airports) == 2
    iata_codes = {a.iata for a in result.destination_airports}
    assert "GOI" in iata_codes
    assert "GOX" in iata_codes

    # Flight candidates collected independently
    assert len(result.outbound_flights) == 1
    assert result.outbound_flights[0].origin_iata == "DEL"
    assert result.outbound_flights[0].destination_iata == "GOI"
    assert result.outbound_flights[0].price_amount == 4200.0

    assert len(result.return_flights) == 1
    assert result.return_flights[0].origin_iata == "GOI"
    assert result.return_flights[0].destination_iata == "DEL"

    # Hotel candidates with multiple room offers and sandbox status
    assert len(result.hotels) == 1
    hotel = result.hotels[0]
    assert hotel.hotel_id == "lp_hotel_1"
    assert hotel.name == "Taj Fort Aguada Resort"
    assert hotel.is_sandbox is True
    assert hotel.min_price_total == 6000.0
    assert len(hotel.offers) == 2
    assert hotel.offers[0].board_name == "Room Only"
    assert hotel.offers[1].board_name == "Bed and Breakfast"
    assert hotel.offers[1].cancellation_policy == "Free cancellation until Dec 10"

    # Tourist places collected
    assert len(result.places) == 2
    assert result.places[0].name == "Fort Aguada"

    # Place-to-place distance matrix
    assert result.places_distance_matrix is not None
    assert result.places_distance_matrix.is_estimated is False
    assert result.places_distance_matrix.routing_provider == "osrm"

    # Diagnostics
    assert result.provider_statuses["geocoding"].status == "success"
    assert result.provider_statuses["flights"].status == "success"
    assert result.provider_statuses["hotels"].status == "success"
    assert result.provider_statuses["places"].status == "success"
    assert result.provider_statuses["routing"].status == "success"


def test_geocoding_failure_continues_flights_and_hotels():
    """Verify geocoding failure marks coordinates/places/routing unavailable but continues flights & hotels."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()
    mock_geoapify.geocode_city.return_value = None  # Geocoding fails

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="UnknownPlace123",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    # Destination coordinates are None
    assert result.destination_coordinates is None

    # Coordinate-dependent places & routing are unavailable
    assert result.places == []
    assert result.places_distance_matrix is None
    assert result.provider_statuses["geocoding"].status == "failed"
    assert result.provider_statuses["places"].status == "unavailable"
    assert result.provider_statuses["routing"].status == "unavailable"

    # Independent flights and city-based hotel searches STILL succeed
    assert len(result.outbound_flights) == 1
    assert len(result.hotels) == 1
    assert result.provider_statuses["flights"].status == "success"
    assert result.provider_statuses["hotels"].status == "success"


def test_same_day_trip_behaviour():
    """Verify same-day trip queries flights on same date and skips hotel search cleanly."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-15",  # Same-day trip
    )

    result = aggregator.aggregate_trip(req)

    assert result.is_same_day is True
    assert result.duration_days == 1

    # Flights searched independently
    assert len(result.outbound_flights) == 1
    assert len(result.return_flights) == 1
    assert result.provider_statuses["flights"].status == "success"

    # Hotel search is skipped without calling Nuitee
    assert result.hotels == []
    assert result.provider_statuses["hotels"].status == "skipped"
    assert "Same-day trip" in result.provider_statuses["hotels"].error_message
    assert not mock_nuitee.search_hotel_rates.called


def test_multi_airport_candidates_preserved_and_searched():
    """Verify multiple airports per city are preserved and combinations are queried."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    # Destination has 2 airports (GOI and GOX)
    assert len(result.destination_airports) == 2
    iatas = [a.iata for a in result.destination_airports]
    assert "GOI" in iatas and "GOX" in iatas

    # Ignav was queried for multiple pairs
    assert mock_ignav.search_one_way_flights.call_count >= 2


def test_hotel_offer_preservation_and_sandbox_status():
    """Verify individual room offers, rates, cancellation policies, and sandbox status are preserved."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    assert len(result.hotels) == 1
    h = result.hotels[0]
    assert isinstance(h, AggregatedHotelOption)
    assert h.is_sandbox is True
    assert h.source_provider == "Nuitee/LiteAPI"
    assert len(h.offers) == 2

    # Offer details
    o1 = h.offers[0]
    assert isinstance(o1, HotelRoomOffer)
    assert o1.offer_id == "offer_standard_1"
    assert o1.room_name == "Standard Room"
    assert o1.total_amount == 6000.0
    assert o1.taxes_and_fees == {"vat": 500.0}

    o2 = h.offers[1]
    assert o2.offer_id == "offer_deluxe_1"
    assert o2.board_name == "Bed and Breakfast"
    assert o2.cancellation_policy == "Free cancellation until Dec 10"


def test_place_deduplication_by_id_and_proximity():
    """Verify places are deduplicated by place_id and spatial proximity (< 75m)."""
    p1 = Place(
        place_id="place_1",
        name="Aguada Fort",
        category="sights",
        latitude=15.4925,
        longitude=73.7736,
        source_provider="Geoapify",
    )
    # Duplicate ID
    p2 = Place(
        place_id="place_1",
        name="Aguada Fort duplicate ID",
        category="sights",
        latitude=15.4925,
        longitude=73.7736,
        source_provider="Geoapify",
    )
    # Duplicate proximity (~10m away, identical normalized name)
    p3 = Place(
        place_id="place_3",
        name="Aguada fort",
        category="heritage",
        latitude=15.49255,
        longitude=73.77365,
        source_provider="Geoapify",
    )
    # Unique distinct place (~15 km away)
    p4 = Place(
        place_id="place_4",
        name="Old Goa Church",
        category="heritage",
        latitude=15.5009,
        longitude=73.9116,
        source_provider="Geoapify",
    )

    deduped = _deduplicate_places([p1, p2, p3, p4])
    assert len(deduped) == 2
    assert deduped[0].place_id == "place_1"
    assert deduped[1].place_id == "place_4"


def test_routing_fallback_on_osrm_failure():
    """Verify OSRM failure yields DurationMatrixResponse with is_estimated=True and haversine provider."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()

    fallback_matrix = DurationMatrixResponse(
        durations_seconds=[[0.0, 1500.0], [1500.0, 0.0]],
        distances_meters=[[0.0, 12000.0], [12000.0, 0.0]],
        sources=[GeoCoordinates(lat=15.4, lon=73.7), GeoCoordinates(lat=15.5, lon=73.8)],
        destinations=[GeoCoordinates(lat=15.4, lon=73.7), GeoCoordinates(lat=15.5, lon=73.8)],
        is_estimated=True,
        routing_provider="haversine_estimate",
    )
    mock_routing.get_distance_matrix.return_value = fallback_matrix

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    assert result.places_distance_matrix is not None
    assert result.places_distance_matrix.is_estimated is True
    assert result.places_distance_matrix.routing_provider == "haversine_estimate"
    assert result.provider_statuses["routing"].details["is_estimated"] is True


def test_partial_provider_failure_flights_down():
    """Verify flight provider failure does not fail hotel or place searches."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()
    mock_ignav.search_one_way_flights.side_effect = IgnavNetworkError("Ignav connection timed out")

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    assert result.outbound_flights == []
    assert result.return_flights == []
    assert result.provider_statuses["flights"].status == "failed"

    # Other providers succeed
    assert len(result.hotels) == 1
    assert len(result.places) == 2
    assert result.provider_statuses["hotels"].status == "success"
    assert result.provider_statuses["places"].status == "success"


def test_partial_provider_failure_hotels_down():
    """Verify hotel provider failure does not fail flight or place searches."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()
    mock_nuitee.search_hotel_rates.side_effect = NuiteeResponseError("Nuitee upstream 502 error")

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    assert result.hotels == []
    assert result.provider_statuses["hotels"].status == "failed"

    # Other providers succeed
    assert len(result.outbound_flights) == 1
    assert len(result.places) == 2
    assert result.provider_statuses["flights"].status == "success"
    assert result.provider_statuses["places"].status == "success"


def test_request_schema_validation_errors():
    """Verify invalid dates, date ordering, and occupancy raise validation errors."""
    with pytest.raises(ValueError, match="end_date cannot be earlier than start_date"):
        TripAggregationRequest(
            destination="Goa",
            start_date="2026-12-20",
            end_date="2026-12-15",
        )

    with pytest.raises(ValueError, match="Dates must be formatted as YYYY-MM-DD"):
        TripAggregationRequest(
            destination="Goa",
            start_date="invalid-date",
            end_date="2026-12-20",
        )

    with pytest.raises(ValueError, match="Child age must be between 0 and 17"):
        TripAggregationRequest(
            destination="Goa",
            start_date="2026-12-15",
            end_date="2026-12-20",
            children=[20],
        )


def test_credential_sanitization_in_errors():
    """Verify API keys are stripped from error messages in provider status."""
    raw_error = "Failed to authenticate with secret_api_key_123 on https://api.provider.com"
    with pytest.MonkeyPatch.context() as mp:
        from backend.app.core.config import settings
        mp.setattr(settings, "IGNAV_API_KEY", "secret_api_key_123")
        sanitized = _sanitize_error(raw_error)
        assert "secret_api_key_123" not in sanitized
        assert "[REDACTED]" in sanitized


def test_flight_deduplication_across_airports():
    """Verify duplicate flight itineraries across queries are deduplicated."""
    mock_ignav, mock_nuitee, mock_geoapify, mock_routing = create_mock_services()

    # Return duplicate itinerary
    duplicate_response = {
        "origin": "DEL",
        "destination": "GOI",
        "departure_date": "2026-12-15",
        "itineraries": [
            MOCK_FLIGHT_RESPONSE_DEL_GOI["itineraries"][0],
            MOCK_FLIGHT_RESPONSE_DEL_GOI["itineraries"][0],  # Exact duplicate
        ],
    }
    mock_ignav.search_one_way_flights.return_value = duplicate_response

    aggregator = TripAggregatorService(
        ignav_service=mock_ignav,
        nuitee_service=mock_nuitee,
        geoapify_service=mock_geoapify,
        routing_service=mock_routing,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    result = aggregator.aggregate_trip(req)

    # Outbound flights should only have 1 deduplicated item
    assert len(result.outbound_flights) == 1


def test_singleton_dependency():
    """Verify get_trip_aggregator_service returns a singleton instance."""
    import backend.app.services.trip_aggregator_service as mod
    mod._trip_aggregator_service_instance = None
    s1 = get_trip_aggregator_service()
    s2 = get_trip_aggregator_service()
    assert s1 is s2
    assert isinstance(s1, TripAggregatorService)
    mod._trip_aggregator_service_instance = None
