"""Unit tests for LangGraph itinerary synthesis, scheduling, and narrative enrichment."""

import json
from unittest.mock import MagicMock, patch
import pytest

from backend.app.schemas.place import Place
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import DurationMatrixResponse
from backend.app.schemas.trip_aggregation import (
    AggregatedFlightOption,
    AggregatedFlightSegment,
    AggregatedHotelOption,
    HotelRoomOffer,
    ProviderExecutionStatus,
    TripAggregationRequest,
    TripAggregationResult,
)
from backend.app.schemas.itinerary import (
    ItineraryGenerationRequest,
    TripItinerary,
)
from ai_engine.services.itinerary_synthesizer import (
    ItinerarySynthesizer,
    get_itinerary_synthesizer,
    haversine_distance_km,
)
from ai_engine.workflows.itinerary_workflow import ItineraryWorkflow


# ──────────────────────────────────────────────────────────────────
#  Fixtures & Mock Factory
# ──────────────────────────────────────────────────────────────────

def make_sample_place(place_id: str, name: str, lat: float, lon: float, category: str = "tourism.sights") -> Place:
    return Place(
        place_id=place_id,
        name=name,
        category=category,
        latitude=lat,
        longitude=lon,
        address=f"{name}, Goa, India",
        city="Goa",
        country="India",
        source_provider="Geoapify",
    )


def make_sample_flight(flight_id: str, direction: str, carrier: str, price: float) -> AggregatedFlightOption:
    return AggregatedFlightOption(
        flight_id=flight_id,
        direction=direction,
        origin_iata="DEL" if direction == "outbound" else "GOI",
        destination_iata="GOI" if direction == "outbound" else "DEL",
        departure_date="2026-12-15" if direction == "outbound" else "2026-12-17",
        carrier=carrier,
        duration_minutes=150,
        price_amount=price,
        currency="INR",
        cabin_class="economy",
        segments=[
            AggregatedFlightSegment(
                carrier_code="6E",
                flight_number="101",
                departure_airport="DEL" if direction == "outbound" else "GOI",
                arrival_airport="GOI" if direction == "outbound" else "DEL",
                departure_time_local="08:00",
                arrival_time_local="10:30",
            )
        ],
    )


def make_sample_hotel(hotel_id: str, name: str, price_total: float, price_night: float) -> AggregatedHotelOption:
    return AggregatedHotelOption(
        hotel_id=hotel_id,
        name=name,
        star_rating=4,
        user_rating=8.7,
        address="Calangute, Goa",
        latitude=15.543,
        longitude=73.755,
        min_price_total=price_total,
        min_price_per_night=price_night,
        currency="INR",
        is_sandbox=True,
        offers=[
            HotelRoomOffer(
                offer_id=f"offer_{hotel_id}",
                room_name="Deluxe Sea View",
                board_name="Bed & Breakfast",
                total_amount=price_total,
                currency="INR",
                cancellation_policy="FREE_CANCELLATION",
            )
        ],
    )


@pytest.fixture
def sample_places():
    return [
        make_sample_place("p_aguada", "Aguada Fort", 15.492, 73.773, "tourism.sights"),
        make_sample_place("p_sinquerim", "Sinquerim Beach", 15.498, 73.768, "beach"),
        make_sample_place("p_calangute", "Calangute Beach", 15.543, 73.755, "beach"),
        make_sample_place("p_baga", "Baga Beach", 15.555, 73.751, "beach"),
        make_sample_place("p_anjuna", "Anjuna Flea Market", 15.580, 73.742, "commercial.market"),
        make_sample_place("p_chapora", "Chapora Fort", 15.606, 73.738, "heritage"),
        make_sample_place("p_bom_jesus", "Basilica of Bom Jesus", 15.500, 73.911, "heritage"),
        make_sample_place("p_se_cathedral", "Se Cathedral", 15.503, 73.912, "heritage"),
        make_sample_place("p_dudhsagar", "Dudhsagar Waterfalls", 15.314, 74.314, "nature"),
    ]


@pytest.fixture
def sample_aggregation_result(sample_places):
    coords = [GeoCoordinates(lat=p.latitude, lon=p.longitude) for p in sample_places]
    n = len(coords)
    # Simple simulated matrix: 10 mins (600s) & 5000m between all pairs
    durations = [[0.0 if i == j else 600.0 for j in range(n)] for i in range(n)]
    distances = [[0.0 if i == j else 5000.0 for j in range(n)] for i in range(n)]

    matrix = DurationMatrixResponse(
        durations_seconds=durations,
        distances_meters=distances,
        sources=coords,
        destinations=coords,
        is_estimated=False,
        routing_provider="osrm",
    )

    return TripAggregationResult(
        destination="Goa",
        destination_coordinates=GeoCoordinates(lat=15.4989, lon=73.8278),
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        duration_days=3,
        is_same_day=False,
        outbound_flights=[
            make_sample_flight("f_out_exp", "outbound", "Air India", 5500.0),
            make_sample_flight("f_out_cheap", "outbound", "IndiGo", 4200.0),
        ],
        return_flights=[
            make_sample_flight("f_ret_exp", "return", "Vistara", 6000.0),
            make_sample_flight("f_ret_cheap", "return", "IndiGo", 4500.0),
        ],
        hotels=[
            make_sample_hotel("h_exp", "Luxury Resort Goa", 18000.0, 9000.0),
            make_sample_hotel("h_cheap", "Cozy Sands Hotel", 10000.0, 5000.0),
        ],
        places=sample_places,
        places_distance_matrix=matrix,
        provider_statuses={
            "flights": ProviderExecutionStatus(status="success", item_count=4),
            "hotels": ProviderExecutionStatus(status="success", item_count=2),
            "places": ProviderExecutionStatus(status="success", item_count=9),
            "routing": ProviderExecutionStatus(status="success", item_count=9),
        },
    )


# ──────────────────────────────────────────────────────────────────
#  Tests
# ──────────────────────────────────────────────────────────────────

def test_haversine_distance():
    """Verify haversine formula helper accuracy."""
    # Distance between Aguada Fort (15.492, 73.773) and Sinquerim Beach (15.498, 73.768) is ~0.8 km
    dist = haversine_distance_km(15.492, 73.773, 15.498, 73.768)
    assert 0.5 < dist < 1.5


def test_full_itinerary_synthesis_success(sample_aggregation_result):
    """Test full successful synthesis using mocked Gemini client."""
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "trip_title": "Coastal Charms of Goa",
        "trip_summary": "A 3-day adventure through sun-drenched beaches and historic fortresses.",
        "day_narratives": [
            {
                "day_number": 1,
                "theme_title": "Historic Forts & Scenic Coastline",
                "description": "Start your journey taking in panoramic views and golden sands.",
                "stop_notes": {
                    "p_aguada": "Climb up to the lighthouse for the best Arabian Sea panorama.",
                    "p_sinquerim": "Great spot for watersports and watching local fishing boats.",
                    "p_calangute": "Sample fresh Goan fish curry at the beach shacks.",
                },
            },
            {
                "day_number": 2,
                "theme_title": "Bustling Bazaars & Sunset Vantage",
                "description": "Immerse yourself in northern beach culture and historic ruins.",
                "stop_notes": {
                    "p_baga": "Lively beach strip with vibrant music.",
                    "p_anjuna": "Browse bohemian handicrafts and vintage jewelry.",
                    "p_chapora": "Famous viewpoint overlooking the Chapora river mouth.",
                },
            },
            {
                "day_number": 3,
                "theme_title": "Churches of Old Goa & Cascades",
                "description": "Discover Portuguese colonial grandeur and majestic waterfalls.",
                "stop_notes": {
                    "p_bom_jesus": "Notice the elaborate gilded baroque altar.",
                    "p_se_cathedral": "Admire the Golden Bell and Tuscan cathedral architecture.",
                    "p_dudhsagar": "Majestic multi-tiered waterfalls nestled in the jungle.",
                },
            },
        ],
        "practical_tips": [
            "Rent a scooter or car for convenient inter-beach transit.",
            "Carry light cotton clothing and plenty of sunscreen.",
        ],
    })
    mock_gemini.models.generate_content.return_value = mock_response

    synthesizer = ItinerarySynthesizer(gemini_client=mock_gemini)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        pace="moderate",
        budget=30000.0,
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=sample_aggregation_result)

    assert isinstance(itinerary, TripItinerary)
    assert itinerary.trip_title == "Coastal Charms of Goa"
    assert itinerary.duration_days == 3
    assert len(itinerary.days) == 3

    # Check flight recommendation: cheapest outbound (IndiGo 4200) and cheapest return (IndiGo 4500)
    assert itinerary.selected_outbound_flight is not None
    assert itinerary.selected_outbound_flight.flight_id == "f_out_cheap"
    assert itinerary.selected_outbound_flight.price_amount == 4200.0

    assert itinerary.selected_return_flight is not None
    assert itinerary.selected_return_flight.flight_id == "f_ret_cheap"
    assert itinerary.selected_return_flight.price_amount == 4500.0

    # Check hotel recommendation: cheapest hotel (10000 total)
    assert itinerary.selected_hotel is not None
    assert itinerary.selected_hotel.hotel_id == "h_cheap"
    assert itinerary.selected_hotel.total_price == 10000.0

    # Check stops allocation: moderate pace -> 3 stops per day
    for day in itinerary.days:
        assert len(day.stops) == 3
        # Check stop sequence and provenance
        for stop in day.stops:
            assert stop.stop_number in [1, 2, 3]
            assert stop.routing_provider == "osrm"
            assert stop.activity_notes is not None

        # First stop of each day has 0 travel from previous
        assert day.stops[0].travel_from_previous_minutes == 0.0
        assert day.stops[0].travel_from_previous_km == 0.0
        # Subsequent stops have travel time
        assert day.stops[1].travel_from_previous_minutes > 0.0
        assert day.stops[2].travel_from_previous_minutes > 0.0
        assert day.total_travel_minutes > 0.0

    # Check cost breakdown
    # flights: 4200 + 4500 = 8700, hotel: 10000, activities: 9 stops * 500 = 4500. Total = 23200
    assert itinerary.cost_breakdown.flights_cost == 8700.0
    assert itinerary.cost_breakdown.accommodation_cost == 10000.0
    assert itinerary.cost_breakdown.estimated_activities_cost == 4500.0
    assert itinerary.cost_breakdown.total_estimated_cost == 23200.0
    assert itinerary.cost_breakdown.is_within_budget is True


def test_gemini_hallucinations_discarded(sample_aggregation_result):
    """Test that Gemini cannot invent attractions; unknown place IDs are rejected."""
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    # Gemini tries to inject an invented attraction "invented_eiffel_tower"
    mock_response.text = json.dumps({
        "trip_title": "Goa Trip",
        "trip_summary": "Sunny getaway.",
        "day_narratives": [
            {
                "day_number": 1,
                "theme_title": "Day 1",
                "description": "Exploring sights.",
                "stop_notes": {
                    "p_aguada": "Valid tip for Aguada.",
                    "invented_eiffel_tower": "Hallucinated stop tip.",
                },
            }
        ],
        "practical_tips": ["Tip 1"],
    })
    mock_gemini.models.generate_content.return_value = mock_response

    synthesizer = ItinerarySynthesizer(gemini_client=mock_gemini)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=sample_aggregation_result)

    # Verify no stop in any day has the hallucinated place ID
    all_place_ids = [stop.place_id for day in itinerary.days for stop in day.stops]
    assert "invented_eiffel_tower" not in all_place_ids
    # Valid stop tip was applied
    aguada_stop = next(s for d in itinerary.days for s in d.stops if s.place_id == "p_aguada")
    assert aguada_stop.activity_notes == "Valid tip for Aguada."


def test_gemini_failure_triggers_deterministic_fallback(sample_aggregation_result):
    """Test that API errors from Gemini do not crash itinerary synthesis."""
    mock_gemini = MagicMock()
    mock_gemini.models.generate_content.side_effect = Exception("API rate limit exceeded")

    synthesizer = ItinerarySynthesizer(gemini_client=mock_gemini)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=sample_aggregation_result)

    # Valid Pydantic itinerary returned despite API error
    assert isinstance(itinerary, TripItinerary)
    assert "Goa" in itinerary.trip_title
    assert len(itinerary.days) == 3
    assert len(itinerary.practical_tips) >= 2
    for day in itinerary.days:
        assert len(day.stops) == 3
        assert day.theme_title != ""
        assert day.day_description != ""


def test_gemini_invalid_json_fallback(sample_aggregation_result):
    """Test that malformed JSON from LLM activates the deterministic fallback."""
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "I am sorry, but I cannot assist with this request."
    mock_gemini.models.generate_content.return_value = mock_response

    synthesizer = ItinerarySynthesizer(gemini_client=mock_gemini)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=sample_aggregation_result)
    assert isinstance(itinerary, TripItinerary)
    assert "Goa" in itinerary.trip_title


def test_missing_flights_and_hotels(sample_places):
    """Test synthesis when flights and hotels providers returned no candidates."""
    empty_providers_result = TripAggregationResult(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-16",
        duration_days=2,
        is_same_day=False,
        outbound_flights=[],
        return_flights=[],
        hotels=[],
        places=sample_places[:6],
        places_distance_matrix=None,
        provider_statuses={},
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)  # Uses deterministic fallback
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-16",
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=empty_providers_result)

    assert itinerary.selected_outbound_flight is None
    assert itinerary.selected_return_flight is None
    assert itinerary.selected_hotel is None
    assert itinerary.cost_breakdown.flights_cost is None
    assert itinerary.cost_breakdown.accommodation_cost is None
    assert itinerary.cost_breakdown.total_estimated_cost is None
    assert itinerary.cost_breakdown.is_cost_complete is False
    assert len(itinerary.days) == 2
    assert sum(len(d.stops) for d in itinerary.days) == 6


def test_empty_places_leisure_days():
    """Test synthesis when destination places discovery returns 0 places."""
    empty_places_result = TripAggregationResult(
        destination="Remote Island",
        start_date="2026-12-15",
        end_date="2026-12-16",
        duration_days=2,
        is_same_day=False,
        outbound_flights=[],
        return_flights=[],
        hotels=[],
        places=[],
        places_distance_matrix=None,
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = TripAggregationRequest(
        destination="Remote Island",
        start_date="2026-12-15",
        end_date="2026-12-16",
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=empty_places_result)

    assert len(itinerary.days) == 2
    for day in itinerary.days:
        assert len(day.stops) == 0
        assert "Leisure" in day.theme_title
        assert day.total_travel_minutes == 0.0


def test_same_day_trip(sample_places):
    """Test 1-day trip synthesis: duration_days is 1 and no hotel is selected."""
    same_day_result = TripAggregationResult(
        destination="Jaipur",
        start_date="2026-12-15",
        end_date="2026-12-15",
        duration_days=1,
        is_same_day=True,
        hotels=[make_sample_hotel("h_1", "Jaipur Palace", 4000.0, 4000.0)],
        places=sample_places[:3],
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = TripAggregationRequest(
        destination="Jaipur",
        start_date="2026-12-15",
        end_date="2026-12-15",
    )

    itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=same_day_result)

    assert itinerary.is_same_day is True
    assert itinerary.duration_days == 1
    assert itinerary.selected_hotel is None  # Hotels omitted on same-day trips
    assert len(itinerary.days) == 1
    assert len(itinerary.days[0].stops) == 3


def test_travel_pace_variations(sample_places):
    """Verify that travel pace correctly scales the number of stops per day."""
    result = TripAggregationResult(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-15",
        duration_days=1,
        is_same_day=True,
        places=sample_places,
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)

    # Relaxed = 2 stops
    req_relaxed = TripAggregationRequest(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-15",
        pace="relaxed",
    )
    it_relaxed = synthesizer.synthesize_itinerary(req_relaxed, result)
    assert len(it_relaxed.days[0].stops) == 2

    # Moderate = 3 stops
    req_mod = TripAggregationRequest(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-15",
        pace="moderate",
    )
    it_mod = synthesizer.synthesize_itinerary(req_mod, result)
    assert len(it_mod.days[0].stops) == 3

    # Packed = 4 stops
    req_packed = TripAggregationRequest(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-15",
        pace="packed",
    )
    it_packed = synthesizer.synthesize_itinerary(req_packed, result)
    assert len(it_packed.days[0].stops) == 4


def test_budget_exceeded_flag(sample_aggregation_result):
    """Verify is_within_budget flag calculation."""
    synthesizer = ItinerarySynthesizer(enable_gemini=False)

    # Low budget that will be exceeded
    req_tight = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        budget=5000.0,
    )
    it_tight = synthesizer.synthesize_itinerary(req_tight, sample_aggregation_result)
    assert it_tight.cost_breakdown.is_within_budget is False

    # Generous budget
    req_generous = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        budget=100000.0,
    )
    it_generous = synthesizer.synthesize_itinerary(req_generous, sample_aggregation_result)
    assert it_generous.cost_breakdown.is_within_budget is True

    # No budget specified
    req_none = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
    )
    it_none = synthesizer.synthesize_itinerary(req_none, sample_aggregation_result)
    assert it_none.cost_breakdown.is_within_budget is None


def test_haversine_routing_fallback_when_matrix_missing(sample_places):
    """Test travel times are computed with haversine_estimate when distance matrix is None."""
    result_no_matrix = TripAggregationResult(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-15",
        duration_days=1,
        places=sample_places[:3],
        places_distance_matrix=None,
    )

    mock_routing = MagicMock()
    mock_routing.get_route.side_effect = Exception("OSRM unavailable")

    synthesizer = ItinerarySynthesizer(
        routing_service=mock_routing,
        enable_gemini=False,
    )

    req = TripAggregationRequest(
        destination="Goa",
        start_date="2026-12-15",
        end_date="2026-12-15",
    )

    itinerary = synthesizer.synthesize_itinerary(req, result_no_matrix)

    stops = itinerary.days[0].stops
    assert len(stops) == 3
    # Stops 2 and 3 should have haversine estimate
    assert stops[1].routing_provider == "haversine_estimate"
    assert stops[1].is_estimated_travel is True
    assert stops[1].travel_from_previous_minutes > 0.0
    assert stops[1].travel_from_previous_km > 0.0


def test_itinerary_workflow_langgraph(sample_aggregation_result):
    """Test full LangGraph ItineraryWorkflow execution."""
    mock_aggregator = MagicMock()
    mock_aggregator.aggregate_trip.return_value = sample_aggregation_result

    synthesizer = ItinerarySynthesizer(
        aggregator=mock_aggregator,
        enable_gemini=False,
    )

    workflow = ItineraryWorkflow(
        aggregator=mock_aggregator,
        synthesizer=synthesizer,
    )

    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        pace="moderate",
    )

    itinerary = workflow.run(req)

    assert isinstance(itinerary, TripItinerary)
    assert itinerary.destination == "Goa"
    assert itinerary.duration_days == 3
    assert len(itinerary.days) == 3
    mock_aggregator.aggregate_trip.assert_called_once_with(req)


def test_cost_breakdown_unavailable_components_marked_as_none(sample_places):
    """Verify that unavailable flight or hotel costs are represented as None, not ₹0."""
    result = TripAggregationResult(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        duration_days=3,
        outbound_flights=[],  # Flight search failed or empty
        return_flights=[],
        hotels=[],  # Hotel search failed or empty
        places=sample_places[:3],
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        budget=50000.0,
    )

    itinerary = synthesizer.synthesize_itinerary(req, result)
    cb = itinerary.cost_breakdown

    assert cb.flights_cost is None
    assert cb.accommodation_cost is None
    assert cb.is_cost_complete is False
    assert cb.total_estimated_cost is None
    assert cb.is_within_budget is None


def test_candidate_exposure_multiple_candidates_and_properties(sample_places):
    """Test full candidate lists are exposed and accessible via properties and aliases."""
    outbound_candidates = [
        make_sample_flight("f_out_1", "outbound", "IndiGo", 4000.0),
        make_sample_flight("f_out_2", "outbound", "Air India", 5500.0),
        make_sample_flight("f_out_3", "outbound", "Akasa", 4200.0),
    ]
    return_candidates = [
        make_sample_flight("f_ret_1", "return", "IndiGo", 4300.0),
        make_sample_flight("f_ret_2", "return", "SpiceJet", 4800.0),
    ]
    hotel_candidates = [
        make_sample_hotel("h_1", "Budget Inn", 6000.0, 3000.0),
        make_sample_hotel("h_2", "Luxury Resort", 20000.0, 10000.0),
        make_sample_hotel("h_3", "Boutique Stay", 12000.0, 6000.0),
    ]

    result = TripAggregationResult(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        duration_days=3,
        outbound_flights=outbound_candidates,
        return_flights=return_candidates,
        hotels=hotel_candidates,
        places=sample_places[:3],
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        budget=50000.0,
    )

    itinerary = synthesizer.synthesize_itinerary(req, result)

    # 1. Candidate lists preserved and accessible
    assert len(itinerary.candidate_outbound_flights) == 3
    assert len(itinerary.candidate_return_flights) == 2
    assert len(itinerary.candidate_hotels) == 3

    # 2. Property getters match
    assert itinerary.outbound_flight_candidates == itinerary.candidate_outbound_flights
    assert itinerary.return_flight_candidates == itinerary.candidate_return_flights
    assert itinerary.hotel_candidates == itinerary.candidate_hotels

    # 3. Selected items match best/cheapest and exist in candidate lists
    assert itinerary.selected_outbound_flight is not None
    assert itinerary.selected_outbound_flight.flight_id == "f_out_1"
    assert itinerary.selected_outbound_flight.flight_id in [f.flight_id for f in itinerary.candidate_outbound_flights]

    assert itinerary.selected_return_flight is not None
    assert itinerary.selected_return_flight.flight_id == "f_ret_1"
    assert itinerary.selected_return_flight.flight_id in [f.flight_id for f in itinerary.candidate_return_flights]

    assert itinerary.selected_hotel is not None
    assert itinerary.selected_hotel.hotel_id == "h_1"
    assert itinerary.selected_hotel.hotel_id in [h.hotel_id for h in itinerary.candidate_hotels]

    # 4. Serialization check: model_dump contains all candidate keys
    dumped = itinerary.model_dump()
    assert "candidate_outbound_flights" in dumped
    assert "candidate_return_flights" in dumped
    assert "candidate_hotels" in dumped
    assert len(dumped["candidate_outbound_flights"]) == 3
    assert len(dumped["candidate_hotels"]) == 3


def test_candidate_exposure_empty_lists_and_same_day(sample_places):
    """Test empty candidate lists are handled safely with no fake data or fabrication."""
    result = TripAggregationResult(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-15",
        duration_days=1,
        is_same_day=True,
        outbound_flights=[],
        return_flights=[],
        hotels=[],
        places=sample_places[:2],
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-15",
        budget=10000.0,
    )

    itinerary = synthesizer.synthesize_itinerary(req, result)

    assert itinerary.candidate_outbound_flights == []
    assert itinerary.candidate_return_flights == []
    assert itinerary.candidate_hotels == []
    assert itinerary.selected_outbound_flight is None
    assert itinerary.selected_return_flight is None
    assert itinerary.selected_hotel is None


def test_candidate_exposure_partial_provider_failure(sample_places):
    """Test partial provider failure (flights succeed, hotels fail) keeps flights candidates and handles hotel gracefully."""
    outbound_candidates = [
        make_sample_flight("f_out_1", "outbound", "IndiGo", 4000.0),
    ]

    result = TripAggregationResult(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        duration_days=3,
        outbound_flights=outbound_candidates,
        return_flights=[],
        hotels=[],
        places=sample_places[:3],
        provider_statuses={
            "flights": ProviderExecutionStatus(status="partial", item_count=1),
            "hotels": ProviderExecutionStatus(status="failed", item_count=0, error_message="Nuitee API error"),
        },
    )

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = TripAggregationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        budget=30000.0,
    )

    itinerary = synthesizer.synthesize_itinerary(req, result)

    # Flight candidate exposed
    assert len(itinerary.candidate_outbound_flights) == 1
    assert itinerary.selected_outbound_flight is not None
    assert itinerary.selected_outbound_flight.flight_id == "f_out_1"

    # Return flight and hotels empty
    assert itinerary.candidate_return_flights == []
    assert itinerary.selected_return_flight is None
    assert itinerary.candidate_hotels == []
    assert itinerary.selected_hotel is None

    # Cost breakdown handles partial provider availability correctly
    assert itinerary.cost_breakdown.is_cost_complete is False
    assert itinerary.cost_breakdown.accommodation_cost is None


def test_candidate_exposure_direct_router_endpoint(sample_aggregation_result):
    """Direct unit test of the FastAPI router functions without TestClient or network loopback sockets."""
    from backend.app.api.v1.endpoints.itinerary import generate_itinerary, replan_itinerary
    from backend.app.schemas.itinerary import ItineraryReplanRequest

    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    req = ItineraryGenerationRequest(
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-17",
        budget=50000.0,
    )
    expected_itinerary = synthesizer.synthesize_itinerary(req, sample_aggregation_result)
    mock_workflow.run.return_value = expected_itinerary
    mock_workflow.replan.return_value = expected_itinerary

    # 1. Directly invoke generate_itinerary endpoint function
    generated = generate_itinerary(request=req, workflow=mock_workflow)
    assert isinstance(generated, TripItinerary)
    assert len(generated.candidate_outbound_flights) == 2
    assert len(generated.candidate_return_flights) == 2
    assert len(generated.candidate_hotels) == 2
    assert generated.selected_outbound_flight.flight_id == "f_out_cheap"
    assert generated.selected_hotel.hotel_id == "h_cheap"

    # 2. Directly invoke replan_itinerary endpoint function
    replan_req = ItineraryReplanRequest(
        current_itinerary=generated,
        remove_place_ids=["p_sinquerim"],
    )
    replanned = replan_itinerary(request=replan_req, workflow=mock_workflow)
    assert isinstance(replanned, TripItinerary)
    assert len(replanned.candidate_outbound_flights) == 2
    assert len(replanned.candidate_hotels) == 2



