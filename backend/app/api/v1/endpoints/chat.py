import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.core.logger import logger
from ai_engine.workflows.travel_workflow import TravelWorkflow
from ai_engine.services.conversation_manager import ConversationManager

router = APIRouter()

# Shared singleton instances across requests
_shared_manager: Optional[ConversationManager] = None
_shared_workflow: Optional[TravelWorkflow] = None


def get_conversation_manager() -> ConversationManager:
    """Dependency provider for the shared conversation manager."""
    global _shared_manager
    if _shared_manager is None:
        _shared_manager = ConversationManager()
    return _shared_manager


def get_travel_workflow(
    manager: ConversationManager = Depends(get_conversation_manager),
) -> TravelWorkflow:
    """Dependency provider for the travel workflow."""
    global _shared_workflow
    if _shared_workflow is None:
        _shared_workflow = TravelWorkflow(manager=manager)
    return _shared_workflow


def reset_workflow_instance():
    """Helper to reset shared instances during tests."""
    global _shared_workflow, _shared_manager
    _shared_manager = None
    _shared_workflow = None


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a chat message for travel intent and clarification",
    description="Accepts a user travel request message and returns structured conversation state and next action.",
)
async def process_chat_message(
    request: ChatRequest,
    workflow: TravelWorkflow = Depends(get_travel_workflow),
):
    """Chat endpoint connecting frontend requests to the LangGraph TravelWorkflow."""
    # Ensure a non-empty session ID
    session_id = request.session_id.strip() if request.session_id and request.session_id.strip() else str(uuid.uuid4())

    try:
        output = workflow.run(session_id=session_id, user_message=request.message)
    except Exception as exc:
        logger.error(f"Error running travel workflow for session {session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing failed: {str(exc)}",
        )

    # Check if workflow reported an error
    if output.get("next_action") == "error" or output.get("error"):
        error_msg = output.get("response") or "An error occurred while processing your travel request."
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ChatResponse(
                session_id=output.get("session_id", session_id),
                assistant_message=error_msg,
                planning_status="error",
                missing_fields=[],
                skipped_fields=[],
                extracted_details=None,
            ).model_dump(),
        )

    return ChatResponse(
        session_id=output["session_id"],
        assistant_message=output.get("response", ""),
        planning_status=output.get("next_action", "ask_user"),
        missing_fields=output.get("missing_fields", []),
        skipped_fields=output.get("skipped_fields", []),
        extracted_details={
            "destination": output.get("destination"),
            "duration_days": output.get("duration_days"),
            "budget": output.get("budget"),
            "currency": output.get("currency"),
            "interests": output.get("interests", []),
            "travellers": output.get("travellers"),
            "departure_city": output.get("departure_city"),
            "travel_date": output.get("travel_date"),
        },
    )

