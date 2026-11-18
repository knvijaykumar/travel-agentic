"""Unit and integration tests for the Itinerary Generation API endpoint (POST /api/v1/itinerary/generate)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.itinerary import (
    CostBreakdown,
    FlightBookingRecommendation,
    HotelBookingRecommendation,
    ItineraryDay,
    ItineraryStop,
    TripItinerary,
)
from ai_engine.workflows.itinerary_workflow import (
    ItineraryWorkflow,
    get_itinerary_workflow,
)


@pytest.fixture
def client():
    return TestClient(app)


def make_sample_itinerary(
    destination: str = "Goa",
    start_date: str = "2026-12-15",
    end_date: str = "2026-12-17",
    is_same_day: bool = False,
    include_flight: bool = True,
    include_hotel: bool = True,
) -> TripItinerary:
    stops_day1 = [
        ItineraryStop(
            stop_number=1,
            place_id="p_aguada",
            name="Aguada Fort",
            category="tourism.sights",
            latitude=15.492,
            longitude=73.773,
            time_slot="10:00 - 12:30",
            duration_minutes=120,
            travel_from_previous_minutes=0.0,
            travel_from_previous_km=0.0,
            routing_provider="osrm",
            is_estimated_travel=False,
            activity_notes="Great view of Arabian sea.",
        ),
        ItineraryStop(
            stop_number=2,
            place_id="p_sinquerim",
            name="Sinquerim Beach",
            category="beach",
            latitude=15.498,
            longitude=73.768,
            time_slot="14:00 - 16:30",
            duration_minutes=120,
            travel_from_previous_minutes=10.0,
            travel_from_previous_km=2.5,
            routing_provider="osrm",
            is_estimated_travel=False,
            activity_notes="Relax on the sandy shores.",
        ),
    ]

    day1 = ItineraryDay(
        day_number=1,
        date=start_date,
        theme_title="Coastal Forts & Sands",
        day_description="Explore historical fortifications and pristine coastline.",
        stops=stops_day1,
        total_travel_minutes=10.0,
        total_travel_km=2.5,
    )

    outbound = (
        FlightBookingRecommendation(
            direction="outbound",
            flight_id="f_out_1",
            carrier="IndiGo",
            origin_iata="DEL",
            destination_iata="GOI",
            departure_date=start_date,
            departure_time="08:00",
            arrival_time="10:30",
            price_amount=4200.0,
            currency="INR",
            cabin_class="economy",
        )
        if include_flight
        else None
    )

    return_flight = (
        FlightBookingRecommendation(
            direction="return",
            flight_id="f_ret_1",
            carrier="IndiGo",
            origin_iata="GOI",
            destination_iata="DEL",
            departure_date=end_date,
            departure_time="18:00",
            arrival_time="20:30",
            price_amount=4500.0,
            currency="INR",
            cabin_class="economy",
        )
        if include_flight and not is_same_day
        else None
    )

    hotel = (
        HotelBookingRecommendation(
            hotel_id="h_1",
            name="Sands Beach Resort",
            star_rating=4,
            user_rating=8.8,
            address="Candolim, Goa",
            latitude=15.512,
            longitude=73.762,
            room_name="Superior Double",
            board_name="Bed & Breakfast",
            total_price=12000.0,
            price_per_night=6000.0,
            currency="INR",
            is_sandbox=True,
            cancellation_policy="FREE_CANCELLATION",
        )
        if include_hotel and not is_same_day
        else None
    )

    flights_cost = (
        (outbound.price_amount if outbound else 0.0)
        + (return_flight.price_amount if return_flight else 0.0)
        if include_flight
        else None
    )
    hotel_cost = hotel.total_price if (include_hotel and not is_same_day) else (0.0 if is_same_day else None)
    activities_cost = 1000.0

    is_complete = (flights_cost is not None) and (hotel_cost is not None)
    total_cost = (flights_cost + hotel_cost + activities_cost) if is_complete else None
    within_budget = (total_cost <= 40000.0) if (is_complete and total_cost is not None) else None

    return TripItinerary(
        trip_title=f"Highlights of {destination}",
        destination=destination,
        departure_city="Delhi",
        start_date=start_date,
        end_date=end_date,
        duration_days=1 if is_same_day else 3,
        is_same_day=is_same_day,
        pace="moderate",
        trip_summary="A wonderful journey curated with real flights, accommodation, and attractions.",
        selected_outbound_flight=outbound,
        selected_return_flight=return_flight,
        selected_hotel=hotel,
        days=[day1],
        cost_breakdown=CostBreakdown(
            flights_cost=flights_cost,
            accommodation_cost=hotel_cost,
            estimated_activities_cost=activities_cost,
            total_estimated_cost=total_cost,
            currency="INR",
            budget=40000.0,
            is_within_budget=within_budget,
            is_cost_complete=is_complete,
        ),
        practical_tips=["Carry valid ID.", "Pre-book airport taxi."],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────────────────────────
#  Endpoint Tests
# ──────────────────────────────────────────────────────────────────

def test_generate_itinerary_success(client):
    """Test successful POST /api/v1/itinerary/generate with valid parameters."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    sample_itinerary = make_sample_itinerary()
    mock_workflow.run.return_value = sample_itinerary

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        payload = {
            "destination": "Goa",
            "departure_city": "Delhi",
            "start_date": "2026-12-15",
            "end_date": "2026-12-17",
            "adults": 2,
            "budget": 40000.0,
            "currency": "INR",
            "pace": "moderate",
            "interests": ["beach", "heritage"],
        }
        response = client.post("/api/v1/itinerary/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["destination"] == "Goa"
        assert data["duration_days"] == 3
        assert data["trip_title"] == "Highlights of Goa"
        assert len(data["days"]) == 1
        assert len(data["days"][0]["stops"]) == 2
        assert data["selected_outbound_flight"]["carrier"] == "IndiGo"
        assert data["selected_hotel"]["name"] == "Sands Beach Resort"
        assert data["cost_breakdown"]["total_estimated_cost"] > 0
        assert data["cost_breakdown"]["is_within_budget"] is True
        mock_workflow.run.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_generate_itinerary_invalid_date_ordering(client):
    """Test that end_date earlier than start_date returns 422."""
    payload = {
        "destination": "Goa",
        "start_date": "2026-12-17",
        "end_date": "2026-12-15",
    }
    response = client.post("/api/v1/itinerary/generate", json=payload)
    assert response.status_code == 422
    assert "end_date cannot be earlier than start_date" in response.text


def test_generate_itinerary_missing_required_fields(client):
    """Test that missing required fields return 422."""
    # Missing destination
    response = client.post(
        "/api/v1/itinerary/generate",
        json={"start_date": "2026-12-15", "end_date": "2026-12-17"},
    )
    assert response.status_code == 422

    # Missing start_date
    response = client.post(
        "/api/v1/itinerary/generate",
        json={"destination": "Goa", "end_date": "2026-12-17"},
    )
    assert response.status_code == 422


def test_generate_itinerary_invalid_adults(client):
    """Test that invalid adults count returns 422."""
    payload = {
        "destination": "Goa",
        "start_date": "2026-12-15",
        "end_date": "2026-12-17",
        "adults": 0,
    }
    response = client.post("/api/v1/itinerary/generate", json=payload)
    assert response.status_code == 422


def test_generate_itinerary_invalid_currency(client):
    """Test that invalid currency format returns 422."""
    payload = {
        "destination": "Goa",
        "start_date": "2026-12-15",
        "end_date": "2026-12-17",
        "currency": "RUPEES",
    }
    response = client.post("/api/v1/itinerary/generate", json=payload)
    assert response.status_code == 422


def test_generate_itinerary_partial_provider_failure(client):
    """Test that partial provider outages (e.g. no flights or hotel) return 200 with partial itinerary."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    partial_itinerary = make_sample_itinerary(include_flight=False, include_hotel=False)
    mock_workflow.run.return_value = partial_itinerary

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        payload = {
            "destination": "Goa",
            "start_date": "2026-12-15",
            "end_date": "2026-12-17",
        }
        response = client.post("/api/v1/itinerary/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["selected_outbound_flight"] is None
        assert data["selected_hotel"] is None
        assert data["cost_breakdown"]["flights_cost"] is None
        assert data["cost_breakdown"]["accommodation_cost"] is None
        assert data["cost_breakdown"]["total_estimated_cost"] is None
        assert data["cost_breakdown"]["is_cost_complete"] is False
        assert len(data["days"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_generate_itinerary_same_day_trip(client):
    """Test that a 1-day trip returns 200 with is_same_day=True and no hotel."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    same_day_itinerary = make_sample_itinerary(
        start_date="2026-12-15",
        end_date="2026-12-15",
        is_same_day=True,
        include_hotel=False,
    )
    mock_workflow.run.return_value = same_day_itinerary

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        payload = {
            "destination": "Jaipur",
            "start_date": "2026-12-15",
            "end_date": "2026-12-15",
        }
        response = client.post("/api/v1/itinerary/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_same_day"] is True
        assert data["duration_days"] == 1
        assert data["selected_hotel"] is None
    finally:
        app.dependency_overrides.clear()


def test_generate_itinerary_timeout_error(client):
    """Test that a workflow TimeoutError maps to HTTP 504."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    mock_workflow.run.side_effect = TimeoutError("Aggregation network timeout")

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        payload = {
            "destination": "Goa",
            "start_date": "2026-12-15",
            "end_date": "2026-12-17",
        }
        response = client.post("/api/v1/itinerary/generate", json=payload)
        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_generate_itinerary_upstream_provider_failure(client):
    """Test that an upstream provider failure maps to HTTP 502."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    mock_workflow.run.side_effect = RuntimeError("Upstream provider failure: LiteAPI rate limit")

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        payload = {
            "destination": "Goa",
            "start_date": "2026-12-15",
            "end_date": "2026-12-17",
        }
        response = client.post("/api/v1/itinerary/generate", json=payload)
        assert response.status_code == 502
        assert "upstream provider failure" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_generate_itinerary_unexpected_error(client):
    """Test that unexpected server crashes map to HTTP 500."""
    mock_workflow = MagicMock(spec=ItineraryWorkflow)
    mock_workflow.run.side_effect = Exception("Fatal database corruption")

    app.dependency_overrides[get_itinerary_workflow] = lambda: mock_workflow
    try:
        payload = {
            "destination": "Goa",
            "start_date": "2026-12-15",
            "end_date": "2026-12-17",
        }
        response = client.post("/api/v1/itinerary/generate", json=payload)
        assert response.status_code == 500
        assert "unexpected error" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()

