from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request payload for POST /api/v1/chat."""

    session_id: Optional[str] = Field(
        default=None,
        description="Unique conversation session identifier. If omitted, a new UUID session is generated.",
    )
    message: str = Field(
        ...,
        description="User's natural language travel message",
    )

    @field_validator("message")
    @classmethod
    def validate_message_non_empty(cls, v: str) -> str:
        """Ensure message is not empty or pure whitespace."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or only whitespace")
        return v.strip()


class ChatResponse(BaseModel):
    """Structured response payload returned by POST /api/v1/chat."""

    session_id: str = Field(
        ...,
        description="Session identifier associated with this conversation",
    )
    assistant_message: str = Field(
        ...,
        description="Conversational response or clarification question from the travel agent",
    )
    planning_status: str = Field(
        ...,
        description="Current planning state: 'ask_user' | 'ready_for_planning' | 'error'",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Essential fields still required before an itinerary can be generated",
    )
    skipped_fields: List[str] = Field(
        default_factory=list,
        description="Fields explicitly skipped or declined by the user",
    )
    extracted_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Snapshot of accumulated structured travel preferences",
    )

