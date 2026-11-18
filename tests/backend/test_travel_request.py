import pytest
from pydantic import ValidationError
from backend.app.schemas.travel_request import TravelRequest


def test_valid_travel_request():
    """Verify that a fully specified travel request validates successfully."""
    request = TravelRequest(
        destination="Kyoto",
        duration_days=5,
        travellers=2,
        budget=150000.0,
        currency="JPY",
        interests=["culture", "temples", "culinary"],
        departure_city="Tokyo",
        travel_date="2026-12-01",
    )
    assert request.destination == "Kyoto"
    assert request.duration_days == 5
    assert request.travellers == 2
    assert request.budget == 150000.0
    assert request.currency == "JPY"
    assert request.interests == ["culture", "temples", "culinary"]
    assert request.departure_city == "Tokyo"
    assert request.travel_date == "2026-12-01"


def test_missing_required_destination():
    """Verify that omitting or passing an empty/blank destination raises a ValidationError."""
    # Omitted destination
    with pytest.raises(ValidationError) as exc_info:
        TravelRequest(
            duration_days=3,
            travellers=1,
            budget=20000.0,
        )
    assert "destination" in str(exc_info.value)

    # Empty string destination
    with pytest.raises(ValidationError) as exc_info_empty:
        TravelRequest(
            destination="",
            duration_days=3,
            travellers=1,
            budget=20000.0,
        )
    assert "destination" in str(exc_info_empty.value)

    # Whitespace-only destination
    with pytest.raises(ValidationError) as exc_info_spaces:
        TravelRequest(
            destination="   ",
            duration_days=3,
            travellers=1,
            budget=20000.0,
        )
    assert "destination" in str(exc_info_spaces.value)


def test_zero_or_negative_duration():
    """Verify that duration_days must be strictly greater than 0."""
    # Zero duration
    with pytest.raises(ValidationError) as exc_info_zero:
        TravelRequest(
            destination="Paris",
            duration_days=0,
            travellers=1,
            budget=50000.0,
        )
    assert "duration_days" in str(exc_info_zero.value)

    # Negative duration
    with pytest.raises(ValidationError) as exc_info_neg:
        TravelRequest(
            destination="Paris",
            duration_days=-4,
            travellers=1,
            budget=50000.0,
        )
    assert "duration_days" in str(exc_info_neg.value)


def test_zero_or_negative_budget():
    """Verify that budget must be strictly greater than 0."""
    # Zero budget
    with pytest.raises(ValidationError) as exc_info_zero:
        TravelRequest(
            destination="Goa",
            duration_days=3,
            travellers=2,
            budget=0.0,
        )
    assert "budget" in str(exc_info_zero.value)

    # Negative budget
    with pytest.raises(ValidationError) as exc_info_neg:
        TravelRequest(
            destination="Goa",
            duration_days=3,
            travellers=2,
            budget=-1000.0,
        )
    assert "budget" in str(exc_info_neg.value)


def test_zero_or_negative_travellers():
    """Verify that travellers count must be strictly greater than 0."""
    with pytest.raises(ValidationError) as exc_info_zero:
        TravelRequest(
            destination="Manali",
            duration_days=4,
            travellers=0,
            budget=15000.0,
        )
    assert "travellers" in str(exc_info_zero.value)

    with pytest.raises(ValidationError) as exc_info_neg:
        TravelRequest(
            destination="Manali",
            duration_days=4,
            travellers=-2,
            budget=15000.0,
        )
    assert "travellers" in str(exc_info_neg.value)


def test_default_values():
    """Verify default values and ensure no shared mutable state across instances."""
    req1 = TravelRequest(
        destination="Jaipur",
        duration_days=2,
        travellers=1,
        budget=10000.0,
    )

    # Verify default values
    assert req1.currency == "INR"
    assert req1.interests == []
    assert req1.departure_city is None
    assert req1.travel_date is None

    # Verify safe default_factory: modifying interests in one instance does not affect another
    req2 = TravelRequest(
        destination="Udaipur",
        duration_days=3,
        travellers=2,
        budget=20000.0,
    )
    req1.interests.append("palaces")

    assert req1.interests == ["palaces"]
    assert req2.interests == [], "Interests list must not share mutable state across instances"

