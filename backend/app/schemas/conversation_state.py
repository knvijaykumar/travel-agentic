from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.travel_intent import TravelIntentDraft


class ChatMessage(BaseModel):
    """A single message within a conversation."""
    role: str = Field(..., description="Role of the sender ('user' or 'assistant')")
    content: str = Field(..., description="Message text content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the message was recorded",
    )


def merge_intent_drafts(
    current: TravelIntentDraft,
    incoming: TravelIntentDraft,
) -> TravelIntentDraft:
    """Merge an incoming intent draft into an existing draft.

    Merging Rules:
    1. Non-null scalar fields in incoming overwrite existing fields (updates or corrections).
    2. Null fields in incoming never erase existing known fields.
    3. Unmentioned fields remain unchanged.
    4. Non-empty interests in incoming are appended uniquely to existing interests (preserving order).
    5. Newly skipped fields in incoming are added to skipped_fields.
    6. When a field previously marked as skipped receives a non-null, valid value, it is un-skipped.
    """
    updated_dict = current.model_dump()
    incoming_dict = incoming.model_dump()

    for key, new_val in incoming_dict.items():
        if key == "interests":
            if new_val:
                combined = list(current.interests)
                for item in new_val:
                    if item not in combined:
                        combined.append(item)
                updated_dict["interests"] = combined
        elif key == "skipped_fields":
            pass
        else:
            if new_val is not None:
                updated_dict[key] = new_val

    # Manage skipped fields
    skipped = list(current.skipped_fields)
    for field in incoming.skipped_fields:
        if field not in skipped:
            skipped.append(field)

    # If incoming provides a non-null, valid value for a previously skipped field, clear its skipped status
    for key, new_val in incoming_dict.items():
        if key not in ("interests", "skipped_fields") and new_val is not None:
            if key in skipped:
                skipped.remove(key)

    updated_dict["skipped_fields"] = skipped
    return TravelIntentDraft.model_validate(updated_dict)


class ConversationState(BaseModel):
    """Maintains the ongoing state, message history, and accumulated travel intent for a session."""

    session_id: str = Field(..., description="Unique conversation session identifier")
    intent_draft: TravelIntentDraft = Field(
        default_factory=TravelIntentDraft,
        description="Accumulated travel preferences extracted across all user messages",
    )
    last_asked_field: Optional[str] = Field(
        default=None,
        description="The field for which clarification was most recently requested",
    )
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Chronological record of messages in this session",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Session creation UTC timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last state update UTC timestamp",
    )

    def update_intent(self, new_draft: TravelIntentDraft) -> TravelIntentDraft:
        """Merge a new intent draft into the accumulated intent draft and update timestamp."""
        self.intent_draft = merge_intent_drafts(self.intent_draft, new_draft)
        self.updated_at = datetime.now(timezone.utc)
        return self.intent_draft

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Record a message in the conversation history."""
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = datetime.now(timezone.utc)
        return msg

