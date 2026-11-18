"""LangGraph workflow for end-to-end trip aggregation and itinerary synthesis."""

import logging
from typing import Any, Dict, Optional, TypedDict
from langgraph.graph import StateGraph, END

from backend.app.schemas.trip_aggregation import (
    TripAggregationRequest,
    TripAggregationResult,
)
from backend.app.schemas.itinerary import (
    ItineraryReplanRequest,
    TripItinerary,
)
from backend.app.services.trip_aggregator_service import TripAggregatorService, get_trip_aggregator_service
from ai_engine.services.itinerary_synthesizer import ItinerarySynthesizer, get_itinerary_synthesizer

logger = logging.getLogger(__name__)


class ItineraryWorkflowState(TypedDict, total=False):
    """Typed workflow state for the LangGraph itinerary synthesis flow."""
    request: TripAggregationRequest
    pace: str
    aggregation_result: Optional[TripAggregationResult]
    itinerary: Optional[TripItinerary]
    error: Optional[str]


class ItineraryWorkflow:
    """Encapsulates the LangGraph multi-step itinerary synthesis workflow."""

    def __init__(
        self,
        aggregator: Optional[TripAggregatorService] = None,
        synthesizer: Optional[ItinerarySynthesizer] = None,
    ):
        self.aggregator = aggregator
        self.synthesizer = synthesizer
        self.graph = self._build_graph()

    def _get_aggregator(self) -> TripAggregatorService:
        if self.aggregator is None:
            self.aggregator = get_trip_aggregator_service()
        return self.aggregator

    def _get_synthesizer(self) -> ItinerarySynthesizer:
        if self.synthesizer is None:
            self.synthesizer = get_itinerary_synthesizer()
        return self.synthesizer

    def _aggregate_data_node(self, state: ItineraryWorkflowState) -> Dict[str, Any]:
        """Node 1: Deterministic aggregation of flights, hotels, places and routing."""
        # If aggregation result already supplied (e.g. from prior step or mock), reuse it
        existing_res = state.get("aggregation_result")
        if existing_res is not None:
            return {"aggregation_result": existing_res, "error": None}

        req = state.get("request")
        if not req:
            return {"error": "Missing TripAggregationRequest in workflow state."}

        try:
            aggregator = self._get_aggregator()
            result = aggregator.aggregate_trip(req)
            return {"aggregation_result": result, "error": None}
        except Exception as exc:
            logger.error("Trip aggregation step failed: %s", exc)
            return {"aggregation_result": None, "error": str(exc)}

    def _synthesize_itinerary_node(self, state: ItineraryWorkflowState) -> Dict[str, Any]:
        """Node 2: Pure Python day scheduling + Gemini narrative enrichment."""
        req = state.get("request")
        if not req:
            return {"error": "Missing TripAggregationRequest in workflow state."}

        agg_res = state.get("aggregation_result")

        try:
            synthesizer = self._get_synthesizer()
            itinerary = synthesizer.synthesize_itinerary(request=req, aggregation_result=agg_res)
            return {"itinerary": itinerary, "error": None}
        except Exception as exc:
            logger.error("Itinerary synthesis step failed: %s", exc)
            return {"itinerary": None, "error": str(exc)}

    def _build_graph(self):
        """Assemble and compile the StateGraph."""
        builder = StateGraph(ItineraryWorkflowState)

        builder.add_node("aggregate_data", self._aggregate_data_node)
        builder.add_node("synthesize_itinerary", self._synthesize_itinerary_node)

        builder.set_entry_point("aggregate_data")
        builder.add_edge("aggregate_data", "synthesize_itinerary")
        builder.add_edge("synthesize_itinerary", END)

        return builder.compile()

    def run(
        self,
        request: TripAggregationRequest,
        aggregation_result: Optional[TripAggregationResult] = None,
    ) -> TripItinerary:
        """Execute the itinerary synthesis workflow for a trip request."""
        initial_state: ItineraryWorkflowState = {
            "request": request,
            "pace": request.pace,
            "aggregation_result": aggregation_result,
            "itinerary": None,
            "error": None,
        }

        final_state = self.graph.invoke(initial_state)

        err = final_state.get("error")
        itinerary = final_state.get("itinerary")

        if err and not itinerary:
            raise RuntimeError(f"Itinerary workflow execution failed: {err}")

        if not itinerary:
            raise RuntimeError("Itinerary workflow produced no itinerary output.")

        return itinerary

    def replan(self, request: ItineraryReplanRequest) -> TripItinerary:
        """Execute dynamic itinerary replanning for an existing itinerary."""
        synthesizer = self._get_synthesizer()
        return synthesizer.replan_itinerary(request)


_workflow_instance: Optional[ItineraryWorkflow] = None


def get_itinerary_workflow() -> ItineraryWorkflow:
    """Singleton provider for ItineraryWorkflow."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ItineraryWorkflow()
    return _workflow_instance


