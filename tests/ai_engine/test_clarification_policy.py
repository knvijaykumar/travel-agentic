import pytest

from backend.app.schemas.travel_intent import TravelIntentDraft
from backend.app.schemas.conversation_state import merge_intent_drafts
from ai_engine.workflows.clarification_policy import (
    ClarificationPolicy,
    DEFAULT_ESSENTIAL_FIELDS,
    OPTIONAL_FIELDS,
)


def test_clarification_priority_order():
    """Verify that essential fields are defined in strict priority order."""
    policy = ClarificationPolicy()
    assert policy.essential_fields == [
        "destination",
        "duration_days",
        "budget",
        "travellers",
        "departure_city",
    ]
    assert OPTIONAL_FIELDS == ["travel_date", "interests"]


def test_destination_missing():
    """Verify when destination is missing, it is identified and asked first."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        duration_days=3,
        budget=15000.0,
        travellers=2,
        departure_city="Mumbai",
    )
    missing = policy.get_missing_essential_fields(intent)
    assert missing == ["destination"]
    assert policy.get_highest_priority_missing_field(intent) == "destination"

    question = policy.generate_clarification_question(intent)
    assert "destination" in question.lower()


def test_duration_missing():
    """Verify when destination is known but duration is missing, duration is asked next."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="Goa",
        budget=15000.0,
        travellers=2,
        departure_city="Mumbai",
    )
    missing = policy.get_missing_essential_fields(intent)
    assert missing == ["duration_days"]
    assert policy.get_highest_priority_missing_field(intent) == "duration_days"

    question = policy.generate_clarification_question(intent)
    assert "days" in question.lower()
    assert "goa" in question.lower()


def test_budget_missing():
    """Verify when destination and duration are known, budget is asked next."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="Goa",
        duration_days=3,
        travellers=2,
        departure_city="Mumbai",
    )
    missing = policy.get_missing_essential_fields(intent)
    assert missing == ["budget"]
    assert policy.get_highest_priority_missing_field(intent) == "budget"

    question = policy.generate_clarification_question(intent)
    assert "budget" in question.lower()
    assert "goa" in question.lower()


def test_travellers_missing():
    """Verify when destination, duration, and budget are known, travellers is asked next."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="Goa",
        duration_days=3,
        budget=15000.0,
        departure_city="Mumbai",
    )
    missing = policy.get_missing_essential_fields(intent)
    assert missing == ["travellers"]
    assert policy.get_highest_priority_missing_field(intent) == "travellers"

    question = policy.generate_clarification_question(intent)
    assert "travellers" in question.lower()
    assert "goa" in question.lower()


def test_departure_city_missing():
    """Verify when all fields except departure city are known, departure city is asked."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="Goa",
        duration_days=3,
        budget=15000.0,
        travellers=2,
    )
    missing = policy.get_missing_essential_fields(intent)
    assert missing == ["departure_city"]
    assert policy.get_highest_priority_missing_field(intent) == "departure_city"

    question = policy.generate_clarification_question(intent)
    assert "departing" in question.lower()
    assert "goa" in question.lower()


def test_multiple_fields_missing_asks_only_single_highest_priority_question():
    """Verify that when multiple essential fields are missing, only one question is asked."""
    policy = ClarificationPolicy()
    # Empty intent: all 5 fields missing
    intent = TravelIntentDraft()
    missing = policy.get_missing_essential_fields(intent)
    assert len(missing) == 5
    assert missing == ["destination", "duration_days", "budget", "travellers", "departure_city"]

    # Highest priority is destination
    assert policy.get_highest_priority_missing_field(intent) == "destination"

    question = policy.generate_clarification_question(intent)
    # Question asks only for destination, not budget or duration
    assert "destination" in question.lower()
    assert "budget" not in question.lower()
    assert "how many days" not in question.lower()
    assert "travellers" not in question.lower()


def test_previously_supplied_details_not_requested_again():
    """Verify that once a detail is recorded, it is never requested in subsequent checks."""
    policy = ClarificationPolicy()
    state = TravelIntentDraft()

    # Step 1: user provides destination
    state = merge_intent_drafts(state, TravelIntentDraft(destination="Goa"))
    missing_1 = policy.get_missing_essential_fields(state)
    assert "destination" not in missing_1
    assert policy.get_highest_priority_missing_field(state) == "duration_days"

    # Step 2: user provides duration
    state = merge_intent_drafts(state, TravelIntentDraft(duration_days=3))
    missing_2 = policy.get_missing_essential_fields(state)
    assert "destination" not in missing_2
    assert "duration_days" not in missing_2
    assert policy.get_highest_priority_missing_field(state) == "budget"

    # Step 3: user provides budget
    state = merge_intent_drafts(state, TravelIntentDraft(budget=15000.0, currency="INR"))
    missing_3 = policy.get_missing_essential_fields(state)
    assert "destination" not in missing_3
    assert "duration_days" not in missing_3
    assert "budget" not in missing_3
    assert policy.get_highest_priority_missing_field(state) == "travellers"


def test_user_corrects_detail_without_reasking():
    """Verify user correction updates state and clarification proceeds to next missing field."""
    policy = ClarificationPolicy()
    state = TravelIntentDraft(destination="Goa", duration_days=3)

    # User corrects destination to Manali
    state = merge_intent_drafts(state, TravelIntentDraft(destination="Manali"))
    assert state.destination == "Manali"
    assert state.duration_days == 3

    missing = policy.get_missing_essential_fields(state)
    assert "destination" not in missing
    assert "duration_days" not in missing
    assert policy.get_highest_priority_missing_field(state) == "budget"

    question = policy.generate_clarification_question(state)
    assert "budget" in question.lower()
    assert "manali" in question.lower()
    assert "goa" not in question.lower()


def test_optional_fields_remain_optional():
    """Verify that travel_date and interests are never treated as missing essential fields."""
    policy = ClarificationPolicy()
    # All 5 essential fields provided, but travel_date and interests are None/empty
    intent = TravelIntentDraft(
        destination="Jaipur",
        duration_days=4,
        budget=20000.0,
        travellers=2,
        departure_city="Delhi",
        travel_date=None,
        interests=[],
    )

    missing = policy.get_missing_essential_fields(intent)
    assert missing == []
    assert policy.get_highest_priority_missing_field(intent) is None

    # Confirm completion response is generated, not a clarification question
    resp = policy.generate_clarification_question(intent)
    assert "ready" in resp.lower()
    assert "jaipur" in resp.lower()


def test_invalid_and_empty_values_treated_as_missing():
    """Verify that zero/negative numbers and blank strings are treated as missing."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="   ",  # whitespace only
        duration_days=0,     # invalid duration
        budget=-500.0,       # invalid budget
        travellers=0,        # invalid travellers
        departure_city="",   # empty string
    )

    missing = policy.get_missing_essential_fields(intent)
    assert missing == ["destination", "duration_days", "budget", "travellers", "departure_city"]



from ai_engine.workflows.clarification_policy import detect_skip_intent


def test_detect_skip_intent_phrases():
    """Verify that clear skip statements map to correct field names."""
    # Explicit field mentions
    assert detect_skip_intent("I don't know the duration.") == ["duration_days"]
    assert detect_skip_intent("Skip the duration.") == ["duration_days"]
    assert detect_skip_intent("No budget limit.") == ["budget"]
    assert detect_skip_intent("I don't know who is travelling yet.") == ["travellers"]
    assert detect_skip_intent("Haven't decided departure city.") == ["departure_city"]


def test_detect_skip_intent_contextual_last_asked_field():
    """Verify that vague skip statements map to the last asked field."""
    assert detect_skip_intent("Continue without it.", last_asked_field="duration_days") == ["duration_days"]
    assert detect_skip_intent("Skip this.", last_asked_field="budget") == ["budget"]
    assert detect_skip_intent("I don't know yet.", last_asked_field="travellers") == ["travellers"]
    assert detect_skip_intent("Pass.", last_asked_field="departure_city") == ["departure_city"]


def test_detect_skip_intent_does_not_trigger_on_vague_or_unrelated_input():
    """Verify that normal statements and missing info are NOT treated as skips."""
    assert detect_skip_intent("Hello") == []
    assert detect_skip_intent("I like beaches and adventure") == []
    assert detect_skip_intent("Tell me more about Goa") == []
    assert detect_skip_intent("") == []
    assert detect_skip_intent("Maybe tomorrow", last_asked_field="duration_days") == []


def test_skip_field_tracked_separately_without_fake_defaults():
    """Verify skipped fields are tracked in skipped_fields and actual values remain None."""
    intent = TravelIntentDraft(destination="Goa", skipped_fields=["duration_days"])
    assert intent.duration_days is None
    assert intent.skipped_fields == ["duration_days"]


def test_clarification_policy_ignores_skipped_fields():
    """Verify that clarification policy skips asking for fields in skipped_fields."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="Goa",
        skipped_fields=["duration_days"],
    )

    # Missing essential fields should NOT include duration_days because it was skipped
    missing = policy.get_missing_essential_fields(intent)
    assert "duration_days" not in missing
    assert missing == ["budget", "travellers", "departure_city"]

    # Highest priority missing field moves to budget
    assert policy.get_highest_priority_missing_field(intent) == "budget"

    # Generated question asks for budget, not duration
    question = policy.generate_clarification_question(intent)
    assert "budget" in question.lower()
    assert "days" not in question.lower()


def test_user_provides_previously_skipped_field_clears_skip():
    """Verify that providing a value for a skipped field clears its skipped status."""
    state = TravelIntentDraft(destination="Goa", skipped_fields=["duration_days"])

    # User later provides duration
    update = TravelIntentDraft(duration_days=4)
    merged = merge_intent_drafts(state, update)

    assert merged.duration_days == 4
    assert "duration_days" not in merged.skipped_fields
    assert merged.skipped_fields == []


def test_completion_response_with_skipped_duration():
    """Verify completion response gracefully handles skipped duration without inventing defaults."""
    policy = ClarificationPolicy()
    intent = TravelIntentDraft(
        destination="Goa",
        budget=15000.0,
        currency="INR",
        travellers=2,
        departure_city="Mumbai",
        skipped_fields=["duration_days"],
    )

    # Missing should be empty because duration was skipped and all others provided
    assert policy.get_missing_essential_fields(intent) == []

    resp = policy.generate_completion_response(intent)
    assert "flexible duration" in resp.lower()
    assert "goa" in resp.lower()
    assert "15,000" in resp
