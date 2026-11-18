from unittest.mock import MagicMock
import pytest

from backend.app.schemas.travel_intent import TravelIntentDraft
from backend.app.schemas.conversation_state import ConversationState, merge_intent_drafts
from ai_engine.services.conversation_manager import ConversationManager
from ai_engine.services.intent_extractor import TravelIntentExtractor


def test_first_message_creates_state():
    """Verify that a first message initializes a new conversation state."""
    manager = ConversationManager()
    session_id = "session_001"

    draft1 = TravelIntentDraft(destination="Goa")
    state = manager.update_session(session_id, draft1, user_message="I want to visit Goa.")

    assert state.session_id == session_id
    assert state.intent_draft.destination == "Goa"
    assert state.intent_draft.duration_days is None
    assert state.intent_draft.budget is None
    assert len(state.messages) == 1
    assert state.messages[0].content == "I want to visit Goa."


def test_second_message_adds_new_info_and_preserves_existing():
    """Verify that subsequent messages add new information while preserving previously known values."""
    manager = ConversationManager()
    session_id = "session_002"

    # Message 1
    draft1 = TravelIntentDraft(destination="Goa")
    manager.update_session(session_id, draft1, user_message="I want to visit Goa.")

    # Message 2 adds duration
    draft2 = TravelIntentDraft(duration_days=3)
    state = manager.update_session(session_id, draft2, user_message="For 3 days.")

    # Destination is preserved, duration is added
    assert state.intent_draft.destination == "Goa"
    assert state.intent_draft.duration_days == 3
    assert state.intent_draft.budget is None
    assert len(state.messages) == 2


def test_third_message_adds_budget_and_currency():
    """Verify three-step accumulation matching the user's exact specification."""
    manager = ConversationManager()
    session_id = "session_003"

    # Step 1: Destination
    manager.update_session(session_id, TravelIntentDraft(destination="Goa"))
    # Step 2: Duration
    manager.update_session(session_id, TravelIntentDraft(duration_days=3))
    # Step 3: Budget & Currency
    state = manager.update_session(
        session_id,
        TravelIntentDraft(budget=15000.0, currency="INR"),
        user_message="My budget is ₹15,000.",
    )

    assert state.intent_draft.destination == "Goa"
    assert state.intent_draft.duration_days == 3
    assert state.intent_draft.budget == 15000.0
    assert state.intent_draft.currency == "INR"
    assert state.intent_draft.travellers is None


def test_missing_fields_do_not_erase_existing_values():
    """Verify that an incoming draft with null values never overwrites existing known data."""
    current = TravelIntentDraft(
        destination="Kyoto",
        duration_days=5,
        budget=100000.0,
        currency="JPY",
        travellers=2,
    )
    # Incoming draft has ONLY interests, all other fields null
    incoming = TravelIntentDraft(interests=["temples", "zen"])

    merged = merge_intent_drafts(current, incoming)

    assert merged.destination == "Kyoto"
    assert merged.duration_days == 5
    assert merged.budget == 100000.0
    assert merged.currency == "JPY"
    assert merged.travellers == 2
    assert merged.interests == ["temples", "zen"]


def test_corrected_information_replaces_old_information():
    """Verify that explicit corrections overwrite previously stored values."""
    manager = ConversationManager()
    session_id = "session_correction"

    # Initially user planned Goa for 3 days
    manager.update_session(session_id, TravelIntentDraft(destination="Goa", duration_days=3))

    # User changes mind to Manali for 5 days
    state = manager.update_session(
        session_id,
        TravelIntentDraft(destination="Manali", duration_days=5),
        user_message="Actually, change destination to Manali for 5 days.",
    )

    assert state.intent_draft.destination == "Manali"
    assert state.intent_draft.duration_days == 5


def test_different_conversations_do_not_share_state():
    """Verify that separate sessions are strictly isolated in memory."""
    manager = ConversationManager()

    user_a = "user_session_A"
    user_b = "user_session_B"

    manager.update_session(user_a, TravelIntentDraft(destination="Goa", duration_days=3))
    manager.update_session(user_b, TravelIntentDraft(destination="Paris", duration_days=7))

    state_a = manager.get_session(user_a)
    state_b = manager.get_session(user_b)

    assert state_a.intent_draft.destination == "Goa"
    assert state_a.intent_draft.duration_days == 3

    assert state_b.intent_draft.destination == "Paris"
    assert state_b.intent_draft.duration_days == 7

    # Updating A does not affect B
    manager.update_session(user_a, TravelIntentDraft(budget=15000.0))
    assert manager.get_session(user_a).intent_draft.budget == 15000.0
    assert manager.get_session(user_b).intent_draft.budget is None


def test_end_to_end_process_message_with_mock_extractor():
    """Verify end-to-end multi-turn conversation flow with mocked intent extractor."""
    manager = ConversationManager()
    session_id = "e2e_session"

    mock_extractor = MagicMock(spec=TravelIntentExtractor)

    # Turn 1: "I want to visit Goa."
    mock_extractor.extract_intent.return_value = TravelIntentDraft(destination="Goa")
    state1 = manager.process_message(session_id, "I want to visit Goa.", mock_extractor)
    assert state1.intent_draft.destination == "Goa"
    assert state1.intent_draft.duration_days is None

    # Turn 2: "For 3 days."
    mock_extractor.extract_intent.return_value = TravelIntentDraft(duration_days=3)
    state2 = manager.process_message(session_id, "For 3 days.", mock_extractor)
    assert state2.intent_draft.destination == "Goa"
    assert state2.intent_draft.duration_days == 3
    assert state2.intent_draft.budget is None

    # Turn 3: "My budget is ₹15,000."
    mock_extractor.extract_intent.return_value = TravelIntentDraft(budget=15000.0, currency="INR")
    state3 = manager.process_message(session_id, "My budget is ₹15,000.", mock_extractor)
    assert state3.intent_draft.destination == "Goa"
    assert state3.intent_draft.duration_days == 3
    assert state3.intent_draft.budget == 15000.0
    assert state3.intent_draft.currency == "INR"
    assert len(state3.messages) == 3

