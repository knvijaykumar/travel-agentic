from unittest.mock import MagicMock
import pytest

from backend.app.schemas.travel_intent import TravelIntentDraft
from ai_engine.services.intent_extractor import TravelIntentExtractor, IntentExtractionError
from ai_engine.services.conversation_manager import ConversationManager
from ai_engine.workflows.travel_workflow import TravelWorkflow
from ai_engine.workflows.clarification_policy import ClarificationPolicy


def create_mock_extractor(intent_sequence: list = None, raise_error: Exception = None):
    """Helper creating a mocked TravelIntentExtractor that makes 0 real API calls."""
    mock_extractor = MagicMock(spec=TravelIntentExtractor)
    if raise_error:
        mock_extractor.extract_intent.side_effect = raise_error
    elif intent_sequence:
        mock_extractor.extract_intent.side_effect = intent_sequence
    return mock_extractor


def test_workflow_turn_1_missing_duration():
    """Verify Turn 1: Destination extracted, asks for missing duration."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa")
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)

    output = workflow.run(session_id="session_101", user_message="I want to visit Goa.")

    assert output["destination"] == "Goa"
    assert output["duration_days"] is None
    assert output["budget"] is None
    assert output["next_action"] == "ask_user"
    assert "duration_days" in output["missing_fields"]
    assert "days" in output["response"].lower()
    assert "goa" in output["response"].lower()


def test_workflow_consecutive_turn_2_preserves_goa_and_asks_budget():
    """Verify consecutive messages in same session: Goa is preserved, duration added, asks for budget."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(duration_days=3),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "session_102"

    # Turn 1
    workflow.run(session_id=session_id, user_message="I want to visit Goa.")

    # Turn 2 in same session
    output2 = workflow.run(session_id=session_id, user_message="3 days.")

    assert output2["destination"] == "Goa", "Goa must be preserved from Turn 1"
    assert output2["duration_days"] == 3, "Duration must be updated in Turn 2"
    assert output2["budget"] is None
    assert output2["next_action"] == "ask_user"
    assert "budget" in output2["missing_fields"]
    assert "budget" in output2["response"].lower()


def test_workflow_consecutive_turn_3_reaches_ready_for_planning():
    """Verify Turn 3 satisfies all essential fields -> ready_for_planning."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(duration_days=3),
        TravelIntentDraft(budget=15000.0, currency="INR", travellers=2, departure_city="Mumbai"),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "session_103"

    # Turn 1 & 2
    workflow.run(session_id=session_id, user_message="I want to visit Goa.")
    workflow.run(session_id=session_id, user_message="3 days.")

    # Turn 3
    output3 = workflow.run(session_id=session_id, user_message="My budget is ₹15,000 for 2 people departing from Mumbai.")

    assert output3["destination"] == "Goa"
    assert output3["duration_days"] == 3
    assert output3["budget"] == 15000.0
    assert output3["currency"] == "INR"
    assert output3["travellers"] == 2
    assert output3["departure_city"] == "Mumbai"
    assert output3["next_action"] == "ready_for_planning"
    assert output3["missing_fields"] == []
    assert "ready" in output3["response"].lower()


def test_workflow_full_5_turn_clarification_sequence():
    """Verify complete 5-turn clarification journey asking one prioritized question at a time."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(duration_days=3),
        TravelIntentDraft(budget=15000.0, currency="INR"),
        TravelIntentDraft(travellers=2),
        TravelIntentDraft(departure_city="Bangalore"),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "session_5_turns"

    # Turn 1: Destination provided -> Asks duration
    out1 = workflow.run(session_id=session_id, user_message="I want to visit Goa.")
    assert out1["destination"] == "Goa"
    assert "days" in out1["response"].lower()
    assert out1["next_action"] == "ask_user"

    # Turn 2: Duration provided -> Asks budget
    out2 = workflow.run(session_id=session_id, user_message="3 days.")
    assert out2["duration_days"] == 3
    assert "budget" in out2["response"].lower()
    assert out2["next_action"] == "ask_user"

    # Turn 3: Budget provided -> Asks travellers
    out3 = workflow.run(session_id=session_id, user_message="Budget is 15000 INR.")
    assert out3["budget"] == 15000.0
    assert "travellers" in out3["response"].lower()
    assert out3["next_action"] == "ask_user"

    # Turn 4: Travellers provided -> Asks departure city
    out4 = workflow.run(session_id=session_id, user_message="2 people.")
    assert out4["travellers"] == 2
    assert "departing" in out4["response"].lower()
    assert out4["next_action"] == "ask_user"

    # Turn 5: Departure city provided -> All 5 complete!
    out5 = workflow.run(session_id=session_id, user_message="Departing from Bangalore.")
    assert out5["departure_city"] == "Bangalore"
    assert out5["next_action"] == "ready_for_planning"
    assert out5["missing_fields"] == []
    assert "ready" in out5["response"].lower()


def test_workflow_session_isolation():
    """Verify that different session IDs maintain completely separate conversation states."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(destination="Paris"),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)

    out_a = workflow.run(session_id="user_A", user_message="I want to visit Goa.")
    out_b = workflow.run(session_id="user_B", user_message="I want to visit Paris.")

    assert out_a["destination"] == "Goa"
    assert out_b["destination"] == "Paris"


def test_workflow_handles_api_error_without_crashing():
    """Verify that Gemini API errors are caught and returned gracefully without raising unhandled exceptions."""
    mock_extractor = create_mock_extractor(raise_error=IntentExtractionError("Simulated API 503 Overloaded"))
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)

    output = workflow.run(session_id="error_session", user_message="Trip to Tokyo")

    assert output["next_action"] == "error"
    assert "Simulated API 503" in output["error"]
    assert "issue" in output["response"].lower()


def test_workflow_preference_correction():
    """Verify that user corrections overwrite previously stored information in the workflow."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa", duration_days=3),
        TravelIntentDraft(destination="Manali", duration_days=5),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "correction_session"

    workflow.run(session_id=session_id, user_message="Goa for 3 days")
    output2 = workflow.run(session_id=session_id, user_message="Actually, change to Manali for 5 days")

    assert output2["destination"] == "Manali"
    assert output2["duration_days"] == 5



def test_workflow_scenario_skip_duration_continue_without_it():
    """Verify scenario: User declines duration with 'Continue without it.', workflow proceeds to budget."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        # Turn 2: Extractor returns empty/null intent for vague decline
        TravelIntentDraft(),
        # Turn 3: User provides budget
        TravelIntentDraft(budget=15000.0, currency="INR"),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "session_skip_test"

    # Turn 1: "Plan a Goa trip."
    out1 = workflow.run(session_id=session_id, user_message="Plan a Goa trip.")
    assert out1["destination"] == "Goa"
    assert out1["next_action"] == "ask_user"
    assert "days" in out1["response"].lower()

    # Turn 2: "I don't know the exact duration yet. Continue without it."
    out2 = workflow.run(
        session_id=session_id,
        user_message="I don't know the exact duration yet. Continue without it.",
    )
    # 1. Recognises skip
    assert "duration_days" in out2["skipped_fields"]
    # 2. Does NOT invent fake duration
    assert out2["duration_days"] is None
    # 3. Preserves Goa
    assert out2["destination"] == "Goa"
    # 4. Does NOT ask for duration again; proceeds to budget
    assert "days" not in out2["response"].lower()
    assert "budget" in out2["response"].lower()
    assert out2["next_action"] == "ask_user"

    # Turn 3: "My budget is ₹15,000."
    out3 = workflow.run(session_id=session_id, user_message="My budget is ₹15,000.")
    assert out3["budget"] == 15000.0
    # Next missing field should be travellers
    assert "travellers" in out3["response"].lower()


def test_workflow_skip_then_later_provide_duration_clears_skip():
    """Verify that if a user later provides a previously skipped field, its skip status is cleared."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(skipped_fields=["duration_days"]),
        TravelIntentDraft(duration_days=4),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "session_unskip_test"

    # Turn 1
    workflow.run(session_id=session_id, user_message="Plan a Goa trip.")

    # Turn 2: Skip duration
    out2 = workflow.run(session_id=session_id, user_message="Skip the duration.")
    assert "duration_days" in out2["skipped_fields"]
    assert out2["duration_days"] is None

    # Turn 3: User later decides on 4 days
    out3 = workflow.run(session_id=session_id, user_message="Actually, let's do 4 days.")
    assert out3["duration_days"] == 4
    assert "duration_days" not in out3["skipped_fields"]
    assert out3["skipped_fields"] == []


def test_workflow_completes_with_skipped_duration():
    """Verify workflow reaches ready_for_planning even if duration was skipped, given other fields."""
    mock_extractor = create_mock_extractor([
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(skipped_fields=["duration_days"]),
        TravelIntentDraft(budget=15000.0, currency="INR", travellers=2, departure_city="Mumbai"),
    ])
    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    session_id = "session_complete_with_skip"

    # Turn 1
    workflow.run(session_id=session_id, user_message="Goa trip")
    # Turn 2: Skip duration
    workflow.run(session_id=session_id, user_message="Skip duration")
    # Turn 3: Provide remaining fields
    out3 = workflow.run(session_id=session_id, user_message="Budget 15k for 2 from Mumbai")

    assert out3["next_action"] == "ready_for_planning"
    assert out3["duration_days"] is None
    assert "duration_days" in out3["skipped_fields"]
    assert "ready" in out3["response"].lower()
    assert "flexible duration" in out3["response"].lower()
