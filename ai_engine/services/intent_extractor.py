import json
import os
import re
import warnings
from typing import Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai import errors

from backend.app.schemas.travel_intent import TravelIntentDraft
from ai_engine.prompts.intent_prompts import TRAVEL_INTENT_SYSTEM_PROMPT

# Suppress benign internal SDK warning regarding Automatic Function Calling (AFC)
warnings.filterwarnings("ignore", message=".*automatic function calling.*")


class IntentExtractionError(Exception):
    """Raised when intent extraction fails due to API error, malformed JSON, or validation issue."""
    pass


class TravelIntentExtractor:
    """Service that uses Google Gemini to extract structured TravelIntentDraft from natural language."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3.1-flash-lite",
        client: Optional[genai.Client] = None,
    ):
        self.model = model

        if client is not None:
            self.client = client
        else:
            # Load environment if api_key not explicitly passed
            if not api_key:
                env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
                if env_path.exists():
                    load_dotenv(dotenv_path=env_path)
                api_key = os.getenv("GEMINI_API_KEY")

            if not api_key or not api_key.strip():
                raise ValueError(
                    "GEMINI_API_KEY must be provided or configured in backend/.env"
                )

            self.client = genai.Client(api_key=api_key.strip())

    def _clean_json_text(self, raw_text: str) -> str:
        """Strip markdown fences (```json ... ```) or whitespace from LLM output."""
        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def extract_intent(self, user_message: str) -> TravelIntentDraft:
        """Extract structured travel intent from a user's natural language input.

        Args:
            user_message: The raw natural language message from the user.

        Returns:
            A validated TravelIntentDraft instance with extracted (or null) fields.

        Raises:
            IntentExtractionError: If the API call fails or returns unparseable content.
        """
        # Gracefully handle empty or whitespace-only messages without an API call
        if not user_message or not user_message.strip():
            return TravelIntentDraft()

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
            system_instruction=TRAVEL_INTENT_SYSTEM_PROMPT,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_message.strip(),
                config=config,
            )
        except errors.APIError as api_err:
            raise IntentExtractionError(
                f"Gemini API error during intent extraction: {getattr(api_err, 'message', api_err)}"
            ) from api_err
        except Exception as exc:
            raise IntentExtractionError(
                f"Unexpected failure calling Gemini API: {exc}"
            ) from exc

        if not response or not response.text:
            raise IntentExtractionError("Gemini returned an empty response.")

        clean_text = self._clean_json_text(response.text)

        try:
            parsed_dict = json.loads(clean_text)
        except json.JSONDecodeError as decode_err:
            raise IntentExtractionError(
                f"Failed to decode Gemini response as JSON: {decode_err}. Raw text: {clean_text}"
            ) from decode_err

        if not isinstance(parsed_dict, dict):
            raise IntentExtractionError(
                f"Expected JSON object from Gemini, got {type(parsed_dict).__name__}"
            )

        try:
            return TravelIntentDraft.model_validate(parsed_dict)
        except Exception as val_err:
            raise IntentExtractionError(
                f"Pydantic validation failed for extracted intent: {val_err}"
            ) from val_err

