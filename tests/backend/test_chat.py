from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.travel_intent import TravelIntentDraft
from backend.app.api.v1.endpoints.chat import get_travel_workflow, reset_workflow_instance
from ai_engine.services.intent_extractor import TravelIntentExtractor, IntentExtractionError
from ai_engine.services.conversation_manager import ConversationManager
from ai_engine.workflows.travel_workflow import TravelWorkflow


@pytest.fixture(autouse=True)
def clean_state():
    """Reset shared workflow state before and after each test."""
    reset_workflow_instance()
    app.dependency_overrides.clear()
    yield
    reset_workflow_instance()
    app.dependency_overrides.clear()


@pytest.fixture
def test_client():
    """FastAPI TestClient instance."""
    return TestClient(app)


def test_chat_creates_new_session_when_omitted(test_client):
    """Verify that omitting session_id generates a new session and returns structured response."""
    mock_extractor = MagicMock(spec=TravelIntentExtractor)
    mock_extractor.extract_intent.return_value = TravelIntentDraft(destination="Goa")

    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    app.dependency_overrides[get_travel_workflow] = lambda: workflow

    response = test_client.post(
        "/api/v1/chat",
        json={"message": "I want to visit Goa."},
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0
    assert data["planning_status"] == "ask_user"
    assert "duration_days" in data["missing_fields"]
    assert "days" in data["assistant_message"].lower()
    assert data["extracted_details"]["destination"] == "Goa"


def test_chat_multi_turn_preserves_session_state(test_client):
    """Verify multi-turn conversation maintains state across requests using the same session_id."""
    mock_extractor = MagicMock(spec=TravelIntentExtractor)
    mock_extractor.extract_intent.side_effect = [
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(duration_days=3),
    ]

    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    app.dependency_overrides[get_travel_workflow] = lambda: workflow
    session_id = "test_session_multi"

    # Turn 1: Goa
    r1 = test_client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "I want to visit Goa."},
    )
    assert r1.status_code == 200
    assert r1.json()["extracted_details"]["destination"] == "Goa"
    assert "duration_days" in r1.json()["missing_fields"]

    # Turn 2: 3 days in same session
    r2 = test_client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "3 days."},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    # Preserves Goa from Turn 1
    assert d2["extracted_details"]["destination"] == "Goa"
    assert d2["extracted_details"]["duration_days"] == 3
    assert "budget" in d2["missing_fields"]
    assert "budget" in d2["assistant_message"].lower()


def test_chat_session_isolation(test_client):
    """Verify that different session IDs maintain separate conversation states."""
    mock_extractor = MagicMock(spec=TravelIntentExtractor)
    mock_extractor.extract_intent.side_effect = [
        TravelIntentDraft(destination="Goa"),
        TravelIntentDraft(destination="Paris"),
    ]

    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    app.dependency_overrides[get_travel_workflow] = lambda: workflow

    r_a = test_client.post(
        "/api/v1/chat",
        json={"session_id": "session_A", "message": "Trip to Goa"},
    )
    r_b = test_client.post(
        "/api/v1/chat",
        json={"session_id": "session_B", "message": "Trip to Paris"},
    )

    assert r_a.json()["extracted_details"]["destination"] == "Goa"
    assert r_b.json()["extracted_details"]["destination"] == "Paris"


def test_chat_validation_error_on_empty_or_missing_message(test_client):
    """Verify that empty, whitespace, or missing message payloads return 422 Unprocessable Entity."""
    # Empty string
    r1 = test_client.post("/api/v1/chat", json={"message": ""})
    assert r1.status_code == 422

    # Whitespace string
    r2 = test_client.post("/api/v1/chat", json={"message": "   "})
    assert r2.status_code == 422

    # Missing message field
    r3 = test_client.post("/api/v1/chat", json={"session_id": "sess1"})
    assert r3.status_code == 422


def test_chat_workflow_error_status_code(test_client):
    """Verify that workflow extraction errors return HTTP 500 with structured planning_status='error'."""
    mock_extractor = MagicMock(spec=TravelIntentExtractor)
    mock_extractor.extract_intent.side_effect = IntentExtractionError("Simulated API 503 Overload")

    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    app.dependency_overrides[get_travel_workflow] = lambda: workflow

    response = test_client.post(
        "/api/v1/chat",
        json={"message": "Trip to Tokyo"},
    )

    assert response.status_code == 500
    data = response.json()
    assert data["planning_status"] == "error"
    assert "issue" in data["assistant_message"].lower()


def test_chat_workflow_unhandled_crash_returns_500(test_client):
    """Verify that unhandled exceptions in the workflow return HTTP 500 Internal Server Error."""
    mock_workflow = MagicMock(spec=TravelWorkflow)
    mock_workflow.run.side_effect = RuntimeError("Fatal unexpected crash")
    app.dependency_overrides[get_travel_workflow] = lambda: mock_workflow

    response = test_client.post(
        "/api/v1/chat",
        json={"message": "Trip to Tokyo"},
    )

    assert response.status_code == 500
    assert "Workflow processing failed" in response.json()["detail"]


def test_chat_skip_handling_via_api(test_client):
    """Verify that user declining or skipping a detail via API is tracked and ignored in clarification."""
    mock_extractor = MagicMock(spec=TravelIntentExtractor)
    mock_extractor.extract_intent.side_effect = [
        TravelIntentDraft(destination="Goa"),
        # Turn 2: User says "Continue without it", mock returns empty draft
        TravelIntentDraft(),
    ]

    manager = ConversationManager()
    workflow = TravelWorkflow(extractor=mock_extractor, manager=manager)
    app.dependency_overrides[get_travel_workflow] = lambda: workflow
    session_id = "session_skip_api"

    # Turn 1: Goa
    test_client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "Plan a Goa trip."},
    )

    # Turn 2: Decline duration
    r2 = test_client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "I don't know the exact duration yet. Continue without it."},
    )

    assert r2.status_code == 200
    d2 = r2.json()
    assert "duration_days" in d2["skipped_fields"]
    assert d2["extracted_details"]["duration_days"] is None
    assert d2["extracted_details"]["destination"] == "Goa"
    assert "budget" in d2["assistant_message"].lower()
    assert "days" not in d2["assistant_message"].lower()

