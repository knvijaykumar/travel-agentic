import json
from unittest.mock import MagicMock
import pytest

from ai_engine.services.intent_extractor import TravelIntentExtractor, IntentExtractionError
from backend.app.schemas.travel_intent import TravelIntentDraft


def create_mock_client(response_text: str = "", raise_error: Exception = None):
    """Helper to create a mocked google-genai client that avoids real network requests."""
    mock_client = MagicMock()
    if raise_error:
        mock_client.models.generate_content.side_effect = raise_error
    else:
        mock_response = MagicMock()
        mock_response.text = response_text
        mock_client.models.generate_content.return_value = mock_response
    return mock_client


def test_extract_intent_partial_goa_example():
    """Verify extraction matching the prompt's exact example: partial info with missing fields as null."""
    mock_json = json.dumps({
        "destination": "Goa",
        "duration_days": 3,
        "travellers": None,
        "budget": 15000.0,
        "currency": "INR",
        "interests": ["beaches", "adventure"],
        "departure_city": None,
        "travel_date": None,
    })

    client = create_mock_client(response_text=mock_json)
    extractor = TravelIntentExtractor(client=client)

    result = extractor.extract_intent(
        "Plan a 3-day Goa trip under ₹15,000. I like beaches and adventure."
    )

    assert isinstance(result, TravelIntentDraft)
    assert result.destination == "Goa"
    assert result.duration_days == 3
    assert result.budget == 15000.0
    assert result.currency == "INR"
    assert result.interests == ["beaches", "adventure"]
    assert result.travellers is None
    assert result.departure_city is None
    assert result.travel_date is None
    assert result.is_complete is False


def test_extract_intent_complete_info():
    """Verify extraction when all fields are provided."""
    mock_json = json.dumps({
        "destination": "Kyoto",
        "duration_days": 5,
        "travellers": 2,
        "budget": 120000.0,
        "currency": "JPY",
        "interests": ["temples", "culture"],
        "departure_city": "Delhi",
        "travel_date": "2026-12-15",
    })

    client = create_mock_client(response_text=mock_json)
    extractor = TravelIntentExtractor(client=client)

    result = extractor.extract_intent(
        "2 people traveling from Delhi to Kyoto for 5 days starting 2026-12-15, budget 120000 JPY for temples and culture"
    )

    assert result.destination == "Kyoto"
    assert result.duration_days == 5
    assert result.travellers == 2
    assert result.budget == 120000.0
    assert result.currency == "JPY"
    assert result.interests == ["temples", "culture"]
    assert result.departure_city == "Delhi"
    assert result.travel_date == "2026-12-15"
    assert result.is_complete is True


def test_extract_intent_empty_user_message():
    """Verify empty or whitespace-only messages return an empty draft without calling the API."""
    client = create_mock_client(response_text="")
    extractor = TravelIntentExtractor(client=client)

    result_empty = extractor.extract_intent("")
    result_spaces = extractor.extract_intent("    ")

    assert result_empty.destination is None
    assert result_spaces.destination is None
    # Verify no generate_content call was made
    client.models.generate_content.assert_not_called()


def test_extract_intent_markdown_fences():
    """Verify stripping of markdown code fences (```json ... ```) returned by LLM."""
    mock_fenced = """```json
    {
        "destination": "Paris",
        "duration_days": 4,
        "travellers": null,
        "budget": 2000.0,
        "currency": "EUR",
        "interests": ["art", "museums"],
        "departure_city": null,
        "travel_date": null
    }
    ```"""

    client = create_mock_client(response_text=mock_fenced)
    extractor = TravelIntentExtractor(client=client)

    result = extractor.extract_intent("4 days in Paris for 2000 EUR to see art and museums")

    assert result.destination == "Paris"
    assert result.duration_days == 4
    assert result.budget == 2000.0
    assert result.currency == "EUR"
    assert result.interests == ["art", "museums"]


def test_extract_intent_malformed_json():
    """Verify that malformed JSON raises an IntentExtractionError."""
    client = create_mock_client(response_text="Not a JSON string {destination: Goa")
    extractor = TravelIntentExtractor(client=client)

    with pytest.raises(IntentExtractionError) as exc_info:
        extractor.extract_intent("Trip to Goa")

    assert "Failed to decode Gemini response as JSON" in str(exc_info.value)


def test_extract_intent_api_failure():
    """Verify that underlying Gemini API errors are caught and re-raised as IntentExtractionError."""
    client = create_mock_client(raise_error=RuntimeError("Connection reset by peer"))
    extractor = TravelIntentExtractor(client=client)

    with pytest.raises(IntentExtractionError) as exc_info:
        extractor.extract_intent("Trip to Bali")

    assert "Unexpected failure calling Gemini API" in str(exc_info.value)


def test_never_assumes_missing_values():
    """Verify that unstated fields are strictly None, never defaulted."""
    mock_json = json.dumps({
        "destination": "London",
        "duration_days": None,
        "travellers": None,
        "budget": None,
        "currency": None,
        "interests": [],
        "departure_city": None,
        "travel_date": None,
    })

    client = create_mock_client(response_text=mock_json)
    extractor = TravelIntentExtractor(client=client)

    result = extractor.extract_intent("I want to visit London")

    assert result.destination == "London"
    assert result.duration_days is None
    assert result.travellers is None
    assert result.budget is None
    assert result.currency is None
    assert result.interests == []
    assert result.departure_city is None
    assert result.travel_date is None

