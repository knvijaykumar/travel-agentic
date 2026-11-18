from typing import Dict, List, Optional

from backend.app.schemas.conversation_state import ConversationState, merge_intent_drafts
from backend.app.schemas.travel_intent import TravelIntentDraft
from ai_engine.services.intent_extractor import TravelIntentExtractor


class ConversationManager:
    """Manages multi-turn conversation states and isolates sessions from one another in-memory."""

    def __init__(self):
        self._sessions: Dict[str, ConversationState] = {}

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Retrieve the state for a given session ID, or None if not found."""
        return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str) -> ConversationState:
        """Retrieve existing conversation state or initialize a new one for the session ID."""
        if not session_id or not session_id.strip():
            raise ValueError("session_id must be a non-empty string.")

        clean_id = session_id.strip()
        if clean_id not in self._sessions:
            self._sessions[clean_id] = ConversationState(session_id=clean_id)
        return self._sessions[clean_id]

    def update_session(
        self,
        session_id: str,
        new_draft: TravelIntentDraft,
        user_message: Optional[str] = None,
    ) -> ConversationState:
        """Merge a new intent draft into a session's ongoing conversation state."""
        state = self.get_or_create_session(session_id)
        if user_message:
            state.add_message(role="user", content=user_message)
        state.update_intent(new_draft)
        return state

    def process_message(
        self,
        session_id: str,
        user_message: str,
        extractor: TravelIntentExtractor,
    ) -> ConversationState:
        """Process an incoming user message through an extractor and merge into session state.

        1. Retrieves or creates isolated session state.
        2. Records the incoming user message into conversation history.
        3. Extracts the new intent delta using the extractor.
        4. Merges the new delta into the accumulated intent draft (preserving known fields).
        """
        state = self.get_or_create_session(session_id)
        state.add_message(role="user", content=user_message)

        # Extract delta intent from this specific message
        delta_draft = extractor.extract_intent(user_message)

        # Merge delta into the ongoing accumulated state
        state.update_intent(delta_draft)
        return state

    def clear_session(self, session_id: str) -> bool:
        """Reset and remove a session from the manager."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_active_sessions(self) -> List[str]:
        """Return all active session IDs."""
        return list(self._sessions.keys())

    @property
    def session_count(self) -> int:
        """Return the count of active in-memory sessions."""
        return len(self._sessions)

