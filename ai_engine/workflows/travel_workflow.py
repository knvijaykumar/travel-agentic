from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, END

from backend.app.schemas.travel_intent import TravelIntentDraft
from backend.app.schemas.conversation_state import ConversationState
from ai_engine.services.intent_extractor import TravelIntentExtractor, IntentExtractionError
from ai_engine.services.conversation_manager import ConversationManager
from ai_engine.workflows.clarification_policy import (
    ClarificationPolicy,
    DEFAULT_ESSENTIAL_FIELDS,
    detect_skip_intent,
)


class TravelWorkflowState(TypedDict, total=False):
    """Typed workflow state for the LangGraph travel planning flow."""
    session_id: str
    user_message: str
    extracted_intent: Optional[TravelIntentDraft]
    accumulated_intent: Optional[TravelIntentDraft]
    missing_fields: List[str]
    next_action: str  # "ask_user" | "ready_for_planning" | "error"
    response: str
    error: Optional[str]


# Essential fields alias for backward compatibility
ESSENTIAL_FIELDS = DEFAULT_ESSENTIAL_FIELDS


class TravelWorkflow:
    """Encapsulates the LangGraph multi-turn travel intent and clarification workflow."""

    def __init__(
        self,
        extractor: Optional[TravelIntentExtractor] = None,
        manager: Optional[ConversationManager] = None,
        policy: Optional[ClarificationPolicy] = None,
    ):
        self.extractor = extractor
        self.manager = manager if manager is not None else ConversationManager()
        self.policy = policy if policy is not None else ClarificationPolicy()
        self.graph = self._build_graph()

    def _get_extractor(self) -> TravelIntentExtractor:
        """Lazy-load default extractor if not explicitly injected."""
        if self.extractor is None:
            self.extractor = TravelIntentExtractor()
        return self.extractor

    def _extract_intent_node(self, state: TravelWorkflowState) -> Dict[str, Any]:
        """Node 1: Extract structured travel intent and detect explicit skip requests."""
        session_id = state.get("session_id", "default_session")
        user_message = state.get("user_message", "")
        session = self.manager.get_session(session_id)
        last_asked = session.last_asked_field if session else None

        detected_skips = detect_skip_intent(user_message, last_asked)

        try:
            extractor = self._get_extractor()
            extracted = extractor.extract_intent(user_message)
            all_skips = list(extracted.skipped_fields)
            for s in detected_skips:
                if s not in all_skips:
                    all_skips.append(s)
            extracted.skipped_fields = all_skips

            return {
                "extracted_intent": extracted,
                "error": None,
            }
        except Exception as exc:
            # If extraction failed but user explicitly requested a skip, honor the skip
            if detected_skips:
                return {
                    "extracted_intent": TravelIntentDraft(skipped_fields=detected_skips),
                    "error": None,
                }
            return {
                "extracted_intent": None,
                "error": str(exc),
                "next_action": "error",
            }

    def _update_state_node(self, state: TravelWorkflowState) -> Dict[str, Any]:
        """Node 2: Merge the extracted delta into the isolated session state."""
        session_id = state.get("session_id", "default_session")
        user_message = state.get("user_message", "")
        extracted = state.get("extracted_intent")
        error = state.get("error")

        if error or extracted is None:
            # If extraction failed, retain existing state without merging empty delta
            existing_session = self.manager.get_or_create_session(session_id)
            return {
                "accumulated_intent": existing_session.intent_draft,
            }

        # Merge new extracted intent into conversation state
        updated_session = self.manager.update_session(
            session_id=session_id,
            new_draft=extracted,
            user_message=user_message,
        )

        return {
            "accumulated_intent": updated_session.intent_draft,
        }

    def _evaluate_missing_info_node(self, state: TravelWorkflowState) -> Dict[str, Any]:
        """Node 3: Identify which essential travel details are still missing using clarification policy."""
        if state.get("error"):
            return {
                "missing_fields": [],
                "next_action": "error",
            }

        accumulated = state.get("accumulated_intent")
        if not accumulated:
            accumulated = TravelIntentDraft()

        # Skips are ignored by default so clarification focuses only on actionable missing fields
        missing = self.policy.get_missing_essential_fields(accumulated)
        next_action = "ready_for_planning" if not missing else "ask_user"

        return {
            "missing_fields": missing,
            "next_action": next_action,
        }

    def _generate_response_node(self, state: TravelWorkflowState) -> Dict[str, Any]:
        """Node 4: Formulate a conversational response based on next action and missing info."""
        session_id = state.get("session_id", "default_session")
        error = state.get("error")
        next_action = state.get("next_action", "ask_user")
        missing_fields = state.get("missing_fields", [])
        accumulated = state.get("accumulated_intent") or TravelIntentDraft()

        session = self.manager.get_session(session_id)

        if next_action == "error" or error:
            return {
                "response": "I encountered an issue processing your travel request. Could you please rephrase or try again?"
            }

        if next_action == "ready_for_planning":
            if session:
                session.last_asked_field = None
            return {
                "response": self.policy.generate_completion_response(accumulated)
            }

        # Next action is "ask_user": Prioritize the highest-priority missing field
        first_missing = missing_fields[0] if missing_fields else None
        if session:
            session.last_asked_field = first_missing

        response = self.policy.generate_clarification_question(accumulated)
        return {"response": response}

    def _route_next_step(self, state: TravelWorkflowState) -> str:
        """Conditional routing based on next_action."""
        return state.get("next_action", "ask_user")

    def _build_graph(self):
        """Assemble and compile the StateGraph."""
        builder = StateGraph(TravelWorkflowState)

        # 1. Add functional nodes
        builder.add_node("extract_intent", self._extract_intent_node)
        builder.add_node("update_state", self._update_state_node)
        builder.add_node("evaluate_missing_info", self._evaluate_missing_info_node)
        builder.add_node("generate_response", self._generate_response_node)

        # 2. Establish linear pipeline from extraction to evaluation
        builder.set_entry_point("extract_intent")
        builder.add_edge("extract_intent", "update_state")
        builder.add_edge("update_state", "evaluate_missing_info")

        # 3. Add conditional edge from evaluation to response node
        builder.add_conditional_edges(
            "evaluate_missing_info",
            self._route_next_step,
            {
                "ask_user": "generate_response",
                "ready_for_planning": "generate_response",
                "error": "generate_response",
            },
        )

        # 4. Response completes the turn
        builder.add_edge("generate_response", END)

        return builder.compile()

    def run(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Execute the workflow for a user message within a specific session."""
        initial_state: TravelWorkflowState = {
            "session_id": session_id,
            "user_message": user_message,
            "extracted_intent": None,
            "accumulated_intent": None,
            "missing_fields": [],
            "next_action": "ask_user",
            "response": "",
            "error": None,
        }

        final_state = self.graph.invoke(initial_state)

        accumulated = final_state.get("accumulated_intent") or TravelIntentDraft()

        return {
            "session_id": final_state.get("session_id"),
            "destination": accumulated.destination,
            "duration_days": accumulated.duration_days,
            "budget": accumulated.budget,
            "currency": accumulated.currency,
            "interests": accumulated.interests,
            "travellers": accumulated.travellers,
            "departure_city": accumulated.departure_city,
            "travel_date": accumulated.travel_date,
            "skipped_fields": list(accumulated.skipped_fields),
            "missing_fields": final_state.get("missing_fields", []),
            "next_action": final_state.get("next_action"),
            "response": final_state.get("response"),
            "error": final_state.get("error"),
        }
