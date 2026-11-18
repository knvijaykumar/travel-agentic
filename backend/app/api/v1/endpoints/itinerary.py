"""FastAPI endpoint for generating day-wise travel itineraries."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.itinerary import (
    ItineraryGenerationRequest,
    ItineraryReplanRequest,
    TripItinerary,
)
from ai_engine.workflows.itinerary_workflow import (
    ItineraryWorkflow,
    get_itinerary_workflow,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/itinerary", tags=["Itinerary"])


@router.post(
    "/generate",
    summary="Generate day-wise travel itinerary",
    response_model=TripItinerary,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Itinerary generated successfully"},
        422: {"description": "Validation error in travel parameters"},
        500: {"description": "Internal error during itinerary generation"},
        502: {"description": "Upstream aggregation provider failure"},
        504: {"description": "Timeout during aggregation or synthesis"},
    },
)
def generate_itinerary(
    request: ItineraryGenerationRequest,
    workflow: ItineraryWorkflow = Depends(get_itinerary_workflow),
) -> TripItinerary:
    """Generate a validated day-wise travel itinerary combining flights, hotels, places, routing, and AI narrative."""
    try:
        itinerary = workflow.run(request)
        return itinerary
    except ValueError as val_err:
        logger.warning("Validation error in itinerary generation: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except TimeoutError as to_err:
        logger.error("Timeout during itinerary generation: %s", to_err)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Itinerary generation timed out while fetching provider data.",
        )
    except RuntimeError as run_err:
        err_msg = str(run_err)
        logger.error("Runtime error in itinerary workflow: %s", err_msg)
        if "timeout" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Itinerary generation timed out while fetching provider data.",
            )
        if "upstream" in err_msg.lower() or "provider" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Upstream provider failure: {err_msg}",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate itinerary: {err_msg}",
        )
    except Exception as exc:
        logger.error("Unexpected error in itinerary generation: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during itinerary generation.",
        )


@router.post(
    "/replan",
    summary="Dynamically replan an existing itinerary",
    response_model=TripItinerary,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Itinerary replanned successfully"},
        422: {"description": "Validation error in replanning parameters"},
        500: {"description": "Internal error during itinerary replanning"},
    },
)
def replan_itinerary(
    request: ItineraryReplanRequest,
    workflow: ItineraryWorkflow = Depends(get_itinerary_workflow),
) -> TripItinerary:
    """Dynamically modify an existing itinerary by adding/removing stops, reordering, or updating pace/interests."""
    try:
        updated_itinerary = workflow.replan(request)
        return updated_itinerary
    except ValueError as val_err:
        logger.warning("Validation error in itinerary replanning: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error("Unexpected error in itinerary replanning: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to replan itinerary: {exc}",
        )


