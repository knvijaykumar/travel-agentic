"""Unit and integration tests for Dynamic Itinerary Replanning."""

from datetime import datetime, timezone
import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.place import Place
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import RouteDetail, RouteLeg
from backend.app.schemas.itinerary import (
    AddStopAction,
    CostBreakdown,
    FlightBookingRecommendation,
    HotelBookingRecommendation,
    ItineraryDay,
    ItineraryReplanRequest,
    ItineraryStop,
    TripItinerary,
)
from ai_engine.services.itinerary_synthesizer import (
    ItinerarySynthesizer,
    get_itinerary_synthesizer,
)
from ai_engine.workflows.itinerary_workflow import (
    ItineraryWorkflow,
    get_itinerary_workflow,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_place(place_id: str, name: str, lat: float, lon: float, category: str = "tourism.sights") -> Place:
    return Place(
        place_id=place_id,
        name=name,
        category=category,
        latitude=lat,
        longitude=lon,
        address=f"{name}, Goa",
        city="Goa",
        country="India",
        source_provider="Geoapify",
    )


def make_stop(
    stop_number: int,
    place_id: str,
    name: str,
    lat: float,
    lon: float,
    category: str = "tourism.sights",
    travel_mins: float = 0.0,
    travel_km: float = 0.0,
) -> ItineraryStop:
    return ItineraryStop(
        stop_number=stop_number,
        place_id=place_id,
        name=name,
        category=category,
        latitude=lat,
        longitude=lon,
        time_slot="10:00 - 12:00",
        duration_minutes=120,
        travel_from_previous_minutes=travel_mins,
        travel_from_previous_km=travel_km,
        routing_provider="osrm",
        is_estimated_travel=False,
        activity_notes=f"Note for {name}",
    )


@pytest.fixture
def base_itinerary():
    day1_stops = [
        make_stop(1, "p_aguada", "Aguada Fort", 15.492, 73.773, "heritage", 0.0, 0.0),
        make_stop(2, "p_sinquerim", "Sinquerim Beach", 15.498, 73.768, "beach", 10.0, 2.5),
        make_stop(3, "p_calangute", "Calangute Beach", 15.543, 73.755, "beach", 15.0, 6.0),
    ]
    day2_stops = [
        make_stop(1, "p_baga", "Baga Beach", 15.555, 73.751, "beach", 0.0, 0.0),
        make_stop(2, "p_anjuna", "Anjuna Market", 15.580, 73.742, "market", 12.0, 4.0),
    ]

    day1 = ItineraryDay(
        day_number=1,
        date="2026-12-15",
        theme_title="Day 1: Coastal Forts",
        day_description="Explore historical fortifications and coastline.",
        stops=day1_stops,
        total_travel_minutes=25.0,
        total_travel_km=8.5,
    )
    day2 = ItineraryDay(
        day_number=2,
        date="2026-12-16",
        theme_title="Day 2: Beach Bazaars",
        day_description="Explore lively beaches and flea markets.",
        stops=day2_stops,
        total_travel_minutes=12.0,
        total_travel_km=4.0,
    )

    outbound = FlightBookingRecommendation(
        direction="outbound",
        flight_id="f_out",
        carrier="IndiGo",
        origin_iata="DEL",
        destination_iata="GOI",
        departure_date="2026-12-15",
        departure_time="08:00",
        arrival_time="10:30",
        price_amount=4000.0,
    )
    ret_flight = FlightBookingRecommendation(
        direction="return",
        flight_id="f_ret",
        carrier="IndiGo",
        origin_iata="GOI",
        destination_iata="DEL",
        departure_date="2026-12-16",
        departure_time="18:00",
        arrival_time="20:30",
        price_amount=4500.0,
    )
    hotel = HotelBookingRecommendation(
        hotel_id="h_1",
        name="Goa Palm Resort",
        room_name="Deluxe Double",
        board_name="Room Only",
        total_price=8000.0,
        price_per_night=4000.0,
    )

    return TripItinerary(
        trip_title="2-Day Goa Explorer",
        destination="Goa",
        departure_city="Delhi",
        start_date="2026-12-15",
        end_date="2026-12-16",
        duration_days=2,
        is_same_day=False,
        pace="moderate",
        trip_summary="A wonderful 2-day journey.",
        selected_outbound_flight=outbound,
        selected_return_flight=ret_flight,
        selected_hotel=hotel,
        days=[day1, day2],
        cost_breakdown=CostBreakdown(
            flights_cost=8500.0,
            accommodation_cost=8000.0,
            estimated_activities_cost=2500.0,  # 5 stops * 500
            total_estimated_cost=19000.0,
            currency="INR",
            budget=30000.0,
            is_within_budget=True,
            is_cost_complete=True,
        ),
        practical_tips=["Carry sunscreen."],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────────────────────────
#  Tests
# ──────────────────────────────────────────────────────────────────

def test_replan_remove_stop(base_itinerary):
    """Test removing a stop updates stop numbers, time slots, and travel metrics."""
    mock_routing = MagicMock()
    # Route from Aguada to Calangute
    mock_routing.get_route.return_value = RouteDetail(
        total_distance_km=7.5,
        total_duration_minutes=18.0,
        routing_provider="osrm",
        is_estimated=False,
    )

    synthesizer = ItinerarySynthesizer(routing_service=mock_routing, enable_gemini=False)
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        remove_place_ids=["p_sinquerim"],
    )

    updated = synthesizer.replan_itinerary(replan_req)

    day1 = updated.days[0]
    assert len(day1.stops) == 2
    assert [s.place_id for s in day1.stops] == ["p_aguada", "p_calangute"]

    # Stop 1
    assert day1.stops[0].stop_number == 1
    assert day1.stops[0].travel_from_previous_minutes == 0.0

    # Stop 2 (Calangute)
    assert day1.stops[1].stop_number == 2
    assert day1.stops[1].travel_from_previous_minutes == 18.0
    assert day1.stops[1].travel_from_previous_km == 7.5

    # Day 1 travel totals
    assert day1.total_travel_minutes == 18.0
    assert day1.total_travel_km == 7.5

    # Total activities cost updated (4 stops * 500 = 2000)
    assert updated.cost_breakdown.estimated_activities_cost == 2000.0
    assert updated.cost_breakdown.total_estimated_cost == 18500.0


def test_replan_add_stop(base_itinerary):
    """Test adding a stop inserts the place and recomputes the route."""
    mock_routing = MagicMock()
    mock_routing.get_route.return_value = RouteDetail(
        total_distance_km=3.0,
        total_duration_minutes=8.0,
        routing_provider="osrm",
        is_estimated=False,
    )

    synthesizer = ItinerarySynthesizer(routing_service=mock_routing, enable_gemini=False)
    new_place = make_place("p_chapora", "Chapora Fort", 15.606, 73.738, "heritage")

    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        add_stops=[
            AddStopAction(day_number=2, place=new_place, position=2)
        ],
    )

    updated = synthesizer.replan_itinerary(replan_req)
    day2 = updated.days[1]

    assert len(day2.stops) == 3
    # Check insertion at position 2
    assert day2.stops[0].place_id == "p_baga"
    assert day2.stops[1].place_id == "p_chapora"
    assert day2.stops[2].place_id == "p_anjuna"

    # Stop indices
    assert [s.stop_number for s in day2.stops] == [1, 2, 3]

    # Activity costs updated (6 stops * 500 = 3000)
    assert updated.cost_breakdown.estimated_activities_cost == 3000.0
    assert updated.cost_breakdown.total_estimated_cost == 19500.0


def test_replan_reorder_stops(base_itinerary):
    """Test explicitly reordering stops on a day."""
    mock_routing = MagicMock()
    mock_routing.get_route.return_value = RouteDetail(
        total_distance_km=5.0,
        total_duration_minutes=12.0,
        routing_provider="osrm",
        is_estimated=False,
    )

    synthesizer = ItinerarySynthesizer(routing_service=mock_routing, enable_gemini=False)
    # Reverse day 1 stops: calangute -> sinquerim -> aguada
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        reorder_days={1: ["p_calangute", "p_sinquerim", "p_aguada"]},
    )

    updated = synthesizer.replan_itinerary(replan_req)
    day1 = updated.days[0]

    assert [s.place_id for s in day1.stops] == ["p_calangute", "p_sinquerim", "p_aguada"]
    assert day1.stops[0].stop_number == 1
    assert day1.stops[0].travel_from_previous_minutes == 0.0
    assert day1.stops[1].stop_number == 2
    assert day1.stops[1].travel_from_previous_minutes == 12.0
    assert day1.stops[2].stop_number == 3


def test_replan_change_pace(base_itinerary):
    """Test changing pace reallocates stops across days."""
    candidates = [
        make_place("p_candolim", "Candolim Beach", 15.517, 73.763, "beach"),
        make_place("p_morjim", "Morjim Beach", 15.632, 73.734, "beach"),
    ]

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    # Change to relaxed pace (2 stops/day)
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        new_pace="relaxed",
        candidate_places=candidates,
    )

    updated = synthesizer.replan_itinerary(replan_req)

    assert updated.pace == "relaxed"
    for day in updated.days:
        assert len(day.stops) == 2


def test_replan_change_interests(base_itinerary):
    """Test updating interests reprioritizes matching places."""
    candidates = [
        make_place("p_bom_jesus", "Basilica of Bom Jesus", 15.500, 73.911, "heritage"),
        make_place("p_se_cathedral", "Se Cathedral", 15.503, 73.912, "heritage"),
    ]

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        new_interests=["heritage"],
        candidate_places=candidates,
    )

    updated = synthesizer.replan_itinerary(replan_req)
    # Heritage attractions should be prioritized
    all_categories = [s.category for d in updated.days for s in d.stops]
    assert "heritage" in all_categories


def test_replan_empty_day_handling(base_itinerary):
    """Test removing all stops on a day cleanly turns it into an unscheduled leisure day."""
    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        remove_place_ids=["p_aguada", "p_sinquerim", "p_calangute"],
    )

    updated = synthesizer.replan_itinerary(replan_req)
    day1 = updated.days[0]

    assert len(day1.stops) == 0
    assert day1.total_travel_minutes == 0.0
    assert day1.total_travel_km == 0.0
    assert "Leisure" in day1.theme_title


def test_replan_duplicate_and_invalid_place_ids(base_itinerary):
    """Test duplicate place additions and invalid reorderings raise ValueError."""
    synthesizer = ItinerarySynthesizer(enable_gemini=False)

    # 1. Duplicate place ID addition
    dup_place = make_place("p_aguada", "Duplicate Aguada", 15.492, 73.773)
    req_dup = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        add_stops=[AddStopAction(day_number=2, place=dup_place)],
    )
    with pytest.raises(ValueError, match="already in the itinerary"):
        synthesizer.replan_itinerary(req_dup)

    # 2. Invalid day in add_stops
    req_bad_day = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        add_stops=[AddStopAction(day_number=99, place=make_place("p_new", "New", 15.0, 73.0))],
    )
    with pytest.raises(ValueError, match="does not exist"):
        synthesizer.replan_itinerary(req_bad_day)

    # 3. Invalid reorder (place ID not currently on that day)
    req_bad_reorder = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        reorder_days={1: ["p_aguada", "p_sinquerim", "unknown_pid"]},
    )
    with pytest.raises(ValueError, match="exact same place IDs"):
        synthesizer.replan_itinerary(req_bad_reorder)


def test_replan_maximum_stops_per_day(base_itinerary):
    """Test adding beyond 5 stops to a single day raises ValueError."""
    synthesizer = ItinerarySynthesizer(enable_gemini=False)

    # Day 1 already has 3 stops. Add stop 4 and stop 5
    p4 = make_place("p_4", "Stop 4", 15.51, 73.76)
    p5 = make_place("p_5", "Stop 5", 15.52, 73.77)
    p6 = make_place("p_6", "Stop 6", 15.53, 73.78)

    # Adding up to 5 is fine
    req_5 = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        add_stops=[
            AddStopAction(day_number=1, place=p4),
            AddStopAction(day_number=1, place=p5),
        ],
    )
    it_5 = synthesizer.replan_itinerary(req_5)
    assert len(it_5.days[0].stops) == 5

    # Adding a 6th stop raises ValueError
    req_6 = ItineraryReplanRequest(
        current_itinerary=it_5,
        add_stops=[AddStopAction(day_number=1, place=p6)],
    )
    with pytest.raises(ValueError, match="maximum of 5 stops"):
        synthesizer.replan_itinerary(req_6)


def test_replan_route_fallback(base_itinerary):
    """Test routing failure triggers Haversine estimate fallback with provenance."""
    mock_routing = MagicMock()
    mock_routing.get_route.side_effect = Exception("OSRM unreachable")

    synthesizer = ItinerarySynthesizer(routing_service=mock_routing, enable_gemini=False)
    # Remove a stop so routing is recalculated
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        remove_place_ids=["p_sinquerim"],
    )

    updated = synthesizer.replan_itinerary(replan_req)
    day1 = updated.days[0]

    assert day1.stops[1].routing_provider == "haversine_estimate"
    assert day1.stops[1].is_estimated_travel is True
    assert day1.stops[1].travel_from_previous_minutes > 0.0
    assert day1.stops[1].travel_from_previous_km > 0.0


def test_replan_unknown_costs_remain_none(base_itinerary):
    """Verify that unknown flight/hotel costs remain None during replanning."""
    # Set flights and hotel costs as None (e.g. provider unavailable)
    base_itinerary.selected_outbound_flight = None
    base_itinerary.selected_hotel = None
    base_itinerary.cost_breakdown.flights_cost = None
    base_itinerary.cost_breakdown.accommodation_cost = None
    base_itinerary.cost_breakdown.is_cost_complete = False
    base_itinerary.cost_breakdown.total_estimated_cost = None
    base_itinerary.cost_breakdown.is_within_budget = None

    synthesizer = ItinerarySynthesizer(enable_gemini=False)
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        remove_place_ids=["p_sinquerim"],
    )

    updated = synthesizer.replan_itinerary(replan_req)
    cb = updated.cost_breakdown

    assert cb.flights_cost is None
    assert cb.accommodation_cost is None
    assert cb.is_cost_complete is False
    assert cb.total_estimated_cost is None
    assert cb.is_within_budget is None
    # Activities cost updated (4 stops * 500 = 2000)
    assert cb.estimated_activities_cost == 2000.0


def test_replan_gemini_failure_deterministic_fallback(base_itinerary):
    """Test that Gemini API failure during replan falls back to deterministic narrative."""
    mock_gemini = MagicMock()
    mock_gemini.models.generate_content.side_effect = Exception("Gemini rate limit exceeded")

    synthesizer = ItinerarySynthesizer(gemini_client=mock_gemini)
    replan_req = ItineraryReplanRequest(
        current_itinerary=base_itinerary,
        remove_place_ids=["p_sinquerim"],
    )

    updated = synthesizer.replan_itinerary(replan_req)

    assert isinstance(updated, TripItinerary)
    assert "Goa" in updated.trip_title
    assert "Day 1" in updated.days[0].theme_title


def test_replan_api_endpoint_success_and_validation_errors(client, base_itinerary):
    """Test POST /api/v1/itinerary/replan HTTP response codes and error handling."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    mock_workflow.replan.return_value = base_itinerary

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        # 1. Success case
        valid_payload = {
            "current_itinerary": base_itinerary.model_dump(),
            "remove_place_ids": ["p_sinquerim"],
        }
        res = client.post("/api/v1/itinerary/replan", json=valid_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["destination"] == "Goa"
        mock_workflow.replan.assert_called_once()

        # 2. Validation error in replan (e.g. ValueError from workflow)
        mock_workflow.replan.side_effect = ValueError("Duplicate place IDs specified in reorder list.")
        res_err = client.post("/api/v1/itinerary/replan", json=valid_payload)
        assert res_err.status_code == 422
        assert "duplicate place ids" in res_err.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()

