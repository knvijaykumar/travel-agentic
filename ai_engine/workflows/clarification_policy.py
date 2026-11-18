"""Clarification policy for identifying missing travel details, handling skips, and asking targeted questions."""

import re
from typing import List, Optional

from backend.app.schemas.travel_intent import TravelIntentDraft


# Essential fields in strictly enforced priority order:
# 1. destination -> 2. duration_days -> 3. budget -> 4. travellers -> 5. departure_city
DEFAULT_ESSENTIAL_FIELDS: List[str] = [
    "destination",
    "duration_days",
    "budget",
    "travellers",
    "departure_city",
]

# Non-essential fields that remain optional and do not block itinerary planning
OPTIONAL_FIELDS: List[str] = [
    "travel_date",
    "interests",
]

# Patterns representing clear refusal, deferral, or skip intents
SKIP_INDICATORS = [
    r"\b(don'?t|do not)\s+know\b",
    r"\bnot\s+sure\b",
    r"\bnot\s+decided\b",
    r"\bno\s+idea\b",
    r"\bhaven'?t\s+decided\b",
    r"\bhave not decided\b",
    r"\byet\s+to\s+decide\b",
    r"\bskip\b",
    r"\bpass\b",
    r"\bcontinue\s+without\b",
    r"\bproceed\s+without\b",
    r"\bwithout\s+(it|this)\b",
    r"\bno\s+preference\b",
    r"\bno\s+budget\b",
    r"\bno\s+limit\b",
    r"\bflexible\b",
    r"\bany\b",
]

# Keywords mapping user statements to specific fields
FIELD_KEYWORDS = {
    "duration_days": [r"\bduration\b", r"\bdays?\b", r"\bhow\s+long\b", r"\blength\b"],
    "budget": [r"\bbudget\b", r"\bmoney\b", r"\bcost\b", r"\bprice\b", r"\bspend(ing)?\b", r"\bamount\b"],
    "travellers": [r"\btravell?ers?\b", r"\btravell?ing\b", r"\bpeople\b", r"\bpersons?\b", r"\bmembers?\b", r"\bheadcount\b", r"\bwho\s+is\s+going\b"],
    "departure_city": [r"\bdeparture\b", r"\bdeparting\b", r"\bleaving\b", r"\borigin\b", r"\bstart\s+city\b"],
    "destination": [r"\bdestination\b", r"\bplace\b", r"\bwhere\b"],
}


def detect_skip_intent(user_message: str, last_asked_field: Optional[str] = None) -> List[str]:
    """Analyze user utterance to detect explicit requests to skip or defer providing travel details.

    Returns a list of field names that the user explicitly indicated they cannot or do not wish to provide.
    Does NOT treat vague statements or missing information as intentional skips.
    """
    if not user_message or not user_message.strip():
        return []

    text = user_message.strip().lower()

    # Verify if an explicit skip or refusal indicator is present
    has_skip_indicator = any(re.search(pat, text) for pat in SKIP_INDICATORS)
    if not has_skip_indicator:
        return []

    detected_fields = []

    # Check if a specific field is mentioned in the skip statement
    for field, patterns in FIELD_KEYWORDS.items():
        if any(re.search(p, text) for p in patterns):
            if field not in detected_fields:
                detected_fields.append(field)

    # If an explicit skip was uttered, but no specific field was named
    # (e.g. "Continue without it", "Skip this", "I don't know yet", "Skip"),
    # attribute the skip to the field currently being clarified.
    if not detected_fields and last_asked_field:
        detected_fields.append(last_asked_field)

    return detected_fields


class ClarificationPolicy:
    """Evaluates missing essential travel information and formulates prioritized clarification prompts."""

    def __init__(self, essential_fields: Optional[List[str]] = None):
        self.essential_fields = (
            list(essential_fields) if essential_fields is not None else list(DEFAULT_ESSENTIAL_FIELDS)
        )

    def is_field_missing(self, intent: Optional[TravelIntentDraft], field: str) -> bool:
        """Check if a specific field is missing, empty, or invalid in the intent draft."""
        if intent is None:
            return True

        if field == "destination":
            return not intent.destination or not str(intent.destination).strip()
        elif field == "duration_days":
            return intent.duration_days is None or intent.duration_days <= 0
        elif field == "budget":
            return intent.budget is None or intent.budget <= 0
        elif field == "travellers":
            return intent.travellers is None or intent.travellers <= 0
        elif field == "departure_city":
            return not intent.departure_city or not str(intent.departure_city).strip()
        return False

    def get_missing_essential_fields(
        self,
        intent: Optional[TravelIntentDraft],
        include_skipped: bool = False,
    ) -> List[str]:
        """Return all essential fields that are currently missing, ordered by priority.
        
        If include_skipped is False (default), fields explicitly marked as skipped by the user
        are ignored so the workflow does not repeatedly query them.
        """
        if intent is None:
            return list(self.essential_fields)

        skipped = set(intent.skipped_fields) if hasattr(intent, "skipped_fields") else set()

        missing = []
        for field in self.essential_fields:
            if not include_skipped and field in skipped:
                continue
            if self.is_field_missing(intent, field):
                missing.append(field)

        return missing

    def get_highest_priority_missing_field(
        self,
        intent: Optional[TravelIntentDraft],
        include_skipped: bool = False,
    ) -> Optional[str]:
        """Return only the single highest-priority missing field, or None if all are present or skipped."""
        missing = self.get_missing_essential_fields(intent, include_skipped=include_skipped)
        return missing[0] if missing else None

    def generate_clarification_question(
        self,
        intent: Optional[TravelIntentDraft],
        missing_field: Optional[str] = None,
    ) -> str:
        """Generate a single focused, conversational question for the highest-priority missing field."""
        if missing_field is None:
            missing_field = self.get_highest_priority_missing_field(intent)

        if missing_field is None:
            return self.generate_completion_response(intent or TravelIntentDraft())

        dest = intent.destination.strip() if (intent and intent.destination) else None
        days = intent.duration_days if (intent and intent.duration_days and intent.duration_days > 0) else None

        if missing_field == "destination":
            return "Where would you like to travel? Please tell me your destination."

        elif missing_field == "duration_days":
            if dest:
                return f"Great choice, {dest}! How many days do you plan to travel?"
            return "How many days do you plan to travel?"

        elif missing_field == "budget":
            if dest and days:
                return f"Got it, a {days}-day trip to {dest}! What is your total budget for this trip?"
            elif dest:
                return f"Understood! What is your total budget for your trip to {dest}?"
            return "What is your total budget for this trip?"

        elif missing_field == "travellers":
            if dest:
                return f"How many travellers will be going on this trip to {dest}?"
            return "How many travellers will be going on this trip?"

        elif missing_field == "departure_city":
            if dest:
                return f"Which city will you be departing from for your trip to {dest}?"
            return "Which city will you be departing from?"

        return "Could you please provide more details about your travel plans?"

    def generate_completion_response(self, intent: TravelIntentDraft) -> str:
        """Formulate confirmation response once all essential details are satisfied or skipped."""
        dest = intent.destination or "your destination"
        curr = intent.currency or "INR"
        budget_str = f"{intent.budget:,.0f}" if intent.budget else "flexible budget"
        travellers = f"{intent.travellers} traveller(s)" if intent.travellers else "flexible group"
        departure = f"departing from {intent.departure_city}" if intent.departure_city else "flexible departure"

        if intent.duration_days and intent.duration_days > 0:
            duration_phrase = f"a {intent.duration_days}-day trip to {dest}"
        else:
            duration_phrase = f"a trip to {dest} (flexible duration)"

        return (
            f"Excellent! I have all key details: {duration_phrase} "
            f"for {travellers} ({departure}) with a budget of {curr} {budget_str}. "
            f"We are ready to plan your itinerary!"
        )
