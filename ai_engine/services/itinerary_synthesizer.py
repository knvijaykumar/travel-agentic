"""Service for synthesizing complete travel itineraries from aggregated trip data."""

import concurrent.futures
from datetime import date, datetime, timedelta, timezone
import json
import logging
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import warnings
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai import errors

from backend.app.core.config import settings
from backend.app.schemas.place import Place
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import DurationMatrixResponse
from backend.app.schemas.trip_aggregation import (
    AggregatedFlightOption,
    AggregatedHotelOption,
    TripAggregationRequest,
    TripAggregationResult,
)
from backend.app.schemas.itinerary import (
    AddStopAction,
    CostBreakdown,
    FlightBookingRecommendation,
    HotelBookingRecommendation,
    ItineraryDay,
    ItineraryReplanRequest,
    ItineraryStop,
    TripItinerary,
)
from backend.app.services.routing_service import RoutingService, get_routing_service
from backend.app.services.trip_aggregator_service import TripAggregatorService, get_trip_aggregator_service
from ai_engine.prompts.itinerary_prompts import ITINERARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Suppress benign internal SDK warning regarding Automatic Function Calling
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

PACE_STOPS_MAP: Dict[str, int] = {
    "relaxed": 2,
    "moderate": 3,
    "packed": 4,
}

TIME_SLOT_TEMPLATES: Dict[int, List[str]] = {
    1: ["10:00 - 13:00"],
    2: ["10:00 - 12:30", "15:00 - 17:30"],
    3: ["09:30 - 11:30", "12:30 - 14:30", "15:30 - 17:30"],
    4: ["09:30 - 11:30", "12:00 - 14:00", "14:30 - 16:30", "17:00 - 18:30"],
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two coordinates in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class ItinerarySynthesizer:
    """Deterministic itinerary scheduler enriched with Gemini natural language narratives."""

    def __init__(
        self,
        aggregator: Optional[TripAggregatorService] = None,
        routing_service: Optional[RoutingService] = None,
        gemini_client: Optional[genai.Client] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_gemini: bool = True,
    ):
        self.aggregator = aggregator
        self.routing_service = routing_service
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash") or "gemini-3.8-flash"
        self.enable_gemini = enable_gemini

        if not enable_gemini:
            self.client = None
        elif gemini_client is not None:
            self.client = gemini_client
        else:
            if not api_key:
                env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
                if env_path.exists():
                    load_dotenv(dotenv_path=env_path)
                api_key = os.getenv("GEMINI_API_KEY")

            if api_key and api_key.strip():
                try:
                    self.client = genai.Client(api_key=api_key.strip())
                except Exception as exc:
                    logger.warning("Could not initialize Gemini Client: %s", exc)
                    self.client = None
            else:
                self.client = None

    def _get_aggregator(self) -> TripAggregatorService:
        if self.aggregator is None:
            self.aggregator = get_trip_aggregator_service()
        return self.aggregator

    def _get_routing_service(self) -> RoutingService:
        if self.routing_service is None:
            self.routing_service = get_routing_service()
        return self.routing_service

    def _clean_json_text(self, raw_text: str) -> str:
        """Strip markdown fences (```json ... ```) or extra whitespace from LLM output."""
        text = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def _get_travel_between(
        self,
        place_a: Place,
        place_b: Place,
        matrix: Optional[DurationMatrixResponse],
    ) -> Tuple[float, float, str, bool]:
        """Determine travel time (mins), distance (km), provider, and estimation flag."""
        # Check matrix lookup if available
        if matrix and matrix.durations_seconds:
            coords_sources = matrix.sources
            coords_dests = matrix.destinations
            idx_a = -1
            idx_b = -1
            for i, coord in enumerate(coords_sources):
                if (
                    abs(coord.lat - place_a.latitude) < 0.0002
                    and abs(coord.lon - place_a.longitude) < 0.0002
                ):
                    idx_a = i
                    break
            for j, coord in enumerate(coords_dests):
                if (
                    abs(coord.lat - place_b.latitude) < 0.0002
                    and abs(coord.lon - place_b.longitude) < 0.0002
                ):
                    idx_b = j
                    break

            if idx_a >= 0 and idx_b >= 0:
                duration_sec = matrix.durations_seconds[idx_a][idx_b]
                if matrix.distances_meters and idx_a < len(matrix.distances_meters):
                    dist_meters = matrix.distances_meters[idx_a][idx_b]
                else:
                    dist_meters = duration_sec * (35.0 * 1000.0 / 3600.0)

                duration_mins = max(round(duration_sec / 60.0, 1), 1.0)
                dist_km = round(dist_meters / 1000.0, 2)
                return duration_mins, dist_km, matrix.routing_provider, matrix.is_estimated

        # Fallback to direct routing service call
        try:
            rs = self._get_routing_service()
            route = rs.get_route(
                GeoCoordinates(lat=place_a.latitude, lon=place_a.longitude),
                GeoCoordinates(lat=place_b.latitude, lon=place_b.longitude),
                fallback_to_haversine=True,
            )
            return (
                max(round(route.total_duration_minutes, 1), 1.0),
                round(route.total_distance_km, 2),
                route.routing_provider,
                route.is_estimated,
            )
        except Exception:
            pass

        # Final fallback: Haversine distance with 1.35 road detour factor at 35 km/h
        straight_km = haversine_distance_km(
            place_a.latitude, place_a.longitude, place_b.latitude, place_b.longitude
        )
        road_km = round(straight_km * 1.35, 2)
        duration_mins = max(round((road_km / 35.0) * 60.0, 1), 1.0)
        return duration_mins, road_km, "haversine_estimate", True

    def _select_flights(
        self,
        outbound_flights: List[AggregatedFlightOption],
        return_flights: List[AggregatedFlightOption],
        is_same_day: bool,
    ) -> Tuple[Optional[FlightBookingRecommendation], Optional[FlightBookingRecommendation]]:
        """Select best candidate flights based on price amount."""
        selected_outbound: Optional[FlightBookingRecommendation] = None
        selected_return: Optional[FlightBookingRecommendation] = None

        if outbound_flights:
            cheapest_out = min(outbound_flights, key=lambda f: f.price_amount)
            dep_time = cheapest_out.segments[0].departure_time_local if cheapest_out.segments else "08:00"
            arr_time = cheapest_out.segments[-1].arrival_time_local if cheapest_out.segments else "10:30"
            selected_outbound = FlightBookingRecommendation(
                direction="outbound",
                flight_id=cheapest_out.flight_id,
                carrier=cheapest_out.carrier,
                origin_iata=cheapest_out.origin_iata,
                destination_iata=cheapest_out.destination_iata,
                departure_date=cheapest_out.departure_date,
                departure_time=dep_time,
                arrival_time=arr_time,
                price_amount=cheapest_out.price_amount,
                currency=cheapest_out.currency,
                cabin_class=cheapest_out.cabin_class,
                source_provider=getattr(cheapest_out, "source_provider", "Ignav"),
                is_indicative=getattr(cheapest_out, "is_indicative", False),
                booking_url=getattr(cheapest_out, "booking_url", None),
            )

        if return_flights:
            cheapest_ret = min(return_flights, key=lambda f: f.price_amount)
            dep_time = cheapest_ret.segments[0].departure_time_local if cheapest_ret.segments else "18:00"
            arr_time = cheapest_ret.segments[-1].arrival_time_local if cheapest_ret.segments else "20:30"
            selected_return = FlightBookingRecommendation(
                direction="return",
                flight_id=cheapest_ret.flight_id,
                carrier=cheapest_ret.carrier,
                origin_iata=cheapest_ret.origin_iata,
                destination_iata=cheapest_ret.destination_iata,
                departure_date=cheapest_ret.departure_date,
                departure_time=dep_time,
                arrival_time=arr_time,
                price_amount=cheapest_ret.price_amount,
                currency=cheapest_ret.currency,
                cabin_class=cheapest_ret.cabin_class,
                source_provider=getattr(cheapest_ret, "source_provider", "Ignav"),
                is_indicative=getattr(cheapest_ret, "is_indicative", False),
                booking_url=getattr(cheapest_ret, "booking_url", None),
            )

        return selected_outbound, selected_return

    def _select_hotel(
        self,
        hotels: List[AggregatedHotelOption],
        is_same_day: bool,
    ) -> Optional[HotelBookingRecommendation]:
        """Select best candidate hotel based on price amount."""
        if is_same_day or not hotels:
            return None

        best_hotel = min(hotels, key=lambda h: h.min_price_total)
        offer = best_hotel.offers[0] if best_hotel.offers else None

        room_name = offer.room_name if offer else "Standard Room"
        board_name = offer.board_name if offer else "Room Only"
        total_price = offer.total_amount if offer else best_hotel.min_price_total
        canc_policy = offer.cancellation_policy if offer else None

        return HotelBookingRecommendation(
            hotel_id=best_hotel.hotel_id,
            name=best_hotel.name,
            star_rating=best_hotel.star_rating,
            user_rating=best_hotel.user_rating,
            address=best_hotel.address,
            latitude=best_hotel.latitude,
            longitude=best_hotel.longitude,
            photo_url=best_hotel.photo_url,
            room_name=room_name,
            board_name=board_name,
            total_price=total_price,
            price_per_night=best_hotel.min_price_per_night,
            currency=best_hotel.currency,
            is_sandbox=best_hotel.is_sandbox,
            cancellation_policy=canc_policy,
        )

    def _schedule_days(
        self,
        places: List[Place],
        duration_days: int,
        start_date: str,
        pace: str,
        interests: List[str],
        matrix: Optional[DurationMatrixResponse],
    ) -> List[ItineraryDay]:
        """Perform spatial clustering, sequencing, time slot assignment and travel calculation."""
        stops_per_day = PACE_STOPS_MAP.get(pace, 3)
        d_start = date.fromisoformat(start_date)

        # Handle empty places gracefully
        if not places:
            empty_days: List[ItineraryDay] = []
            for d in range(duration_days):
                day_date = (d_start + timedelta(days=d)).isoformat()
                empty_days.append(
                    ItineraryDay(
                        day_number=d + 1,
                        date=day_date,
                        theme_title=f"Day {d + 1}: Leisure & Independent Exploration",
                        day_description="Relax and explore local neighborhoods, markets, and culinary spots at your own pace.",
                        stops=[],
                        total_travel_minutes=0.0,
                        total_travel_km=0.0,
                    )
                )
            return empty_days

        # Rank places by interest score
        def interest_score(p: Place) -> int:
            if not interests:
                return 0
            txt = f"{p.category} {p.name}".lower()
            return sum(1 for item in interests if item.lower() in txt)

        ranked_places = sorted(places, key=interest_score, reverse=True)
        max_total_stops = duration_days * stops_per_day
        candidate_places = ranked_places[:max_total_stops]

        # Spatial clustering into duration_days clusters
        unassigned = list(candidate_places)
        day_clusters: List[List[Place]] = [[] for _ in range(duration_days)]

        for d in range(duration_days):
            if not unassigned:
                break
            if d == 0 or not day_clusters[d - 1]:
                seed = unassigned.pop(0)
            else:
                # Pick unassigned place furthest from previous day cluster center for spatial variety
                prev_center_lat = sum(p.latitude for p in day_clusters[d - 1]) / len(day_clusters[d - 1])
                prev_center_lon = sum(p.longitude for p in day_clusters[d - 1]) / len(day_clusters[d - 1])
                furthest_idx = max(
                    range(len(unassigned)),
                    key=lambda i: haversine_distance_km(
                        prev_center_lat,
                        prev_center_lon,
                        unassigned[i].latitude,
                        unassigned[i].longitude,
                    ),
                )
                seed = unassigned.pop(furthest_idx)

            day_cluster = [seed]
            while len(day_cluster) < stops_per_day and unassigned:
                closest_idx = min(
                    range(len(unassigned)),
                    key=lambda i: haversine_distance_km(
                        seed.latitude,
                        seed.longitude,
                        unassigned[i].latitude,
                        unassigned[i].longitude,
                    ),
                )
                day_cluster.append(unassigned.pop(closest_idx))

            day_clusters[d] = day_cluster

        # Distribute any remaining places across days
        dist_idx = 0
        while unassigned:
            day_clusters[dist_idx % duration_days].append(unassigned.pop(0))
            dist_idx += 1

        # Sequence stops within each cluster to minimize travel distance (greedy TSP)
        def sequence_cluster(cluster: List[Place]) -> List[Place]:
            if len(cluster) <= 1:
                return cluster
            seq = [cluster[0]]
            remaining = cluster[1:]
            while remaining:
                curr = seq[-1]
                nxt_idx = min(
                    range(len(remaining)),
                    key=lambda i: haversine_distance_km(
                        curr.latitude,
                        curr.longitude,
                        remaining[i].latitude,
                        remaining[i].longitude,
                    ),
                )
                seq.append(remaining.pop(nxt_idx))
            return seq

        itinerary_days: List[ItineraryDay] = []
        for d in range(duration_days):
            day_date = (d_start + timedelta(days=d)).isoformat()
            raw_cluster = day_clusters[d]
            sequenced_places = sequence_cluster(raw_cluster)
            num_stops = len(sequenced_places)

            # Determine time slots
            time_slots = TIME_SLOT_TEMPLATES.get(num_stops)
            if not time_slots:
                time_slots = [f"{9 + i * 2}:30 - {11 + i * 2}:30" for i in range(num_stops)]

            stops: List[ItineraryStop] = []
            day_travel_mins = 0.0
            day_travel_km = 0.0

            for k, place in enumerate(sequenced_places):
                if k == 0:
                    trav_mins = 0.0
                    trav_km = 0.0
                    provider = "osrm"
                    is_est = False
                else:
                    trav_mins, trav_km, provider, is_est = self._get_travel_between(
                        sequenced_places[k - 1], place, matrix
                    )

                day_travel_mins += trav_mins
                day_travel_km += trav_km

                stops.append(
                    ItineraryStop(
                        stop_number=k + 1,
                        place_id=place.place_id,
                        name=place.name,
                        category=place.category,
                        latitude=place.latitude,
                        longitude=place.longitude,
                        address=place.address,
                        image_url=place.image_url,
                        time_slot=time_slots[k] if k < len(time_slots) else "15:00 - 17:00",
                        duration_minutes=90 if k >= 3 else 120,
                        travel_from_previous_minutes=trav_mins,
                        travel_from_previous_km=trav_km,
                        routing_provider=provider,
                        is_estimated_travel=is_est,
                        activity_notes=None,
                    )
                )

            itinerary_days.append(
                ItineraryDay(
                    day_number=d + 1,
                    date=day_date,
                    theme_title=f"Day {d + 1}: Highlights of {sequenced_places[0].name if sequenced_places else 'City'}",
                    day_description=f"A scenic day exploring {num_stops} signature destination sights.",
                    stops=stops,
                    total_travel_minutes=round(day_travel_mins, 1),
                    total_travel_km=round(day_travel_km, 2),
                )
            )

        return itinerary_days

    def _generate_deterministic_narrative(
        self,
        destination: str,
        days: List[ItineraryDay],
        pace: str,
        interests: List[str],
    ) -> Dict[str, Any]:
        """Deterministic narrative fallback when Gemini is unavailable or returns invalid data."""
        clean_dest = destination.title()
        interest_str = f" emphasizing {', '.join(interests)}" if interests else ""
        trip_title = f"{len(days)}-Day {clean_dest} Explorer"
        trip_summary = (
            f"A curated {pace} {len(days)}-day itinerary showcasing the culture, sights, and highlights of {clean_dest}{interest_str}. "
            f"Designed for smooth transit and memorable experiences across every scheduled day."
        )

        day_narratives = []
        for d in days:
            if d.stops:
                first_name = d.stops[0].name
                theme_title = f"Day {d.day_number}: Highlights around {first_name}"
                stop_names = ", ".join(s.name for s in d.stops[:3])
                description = (
                    f"Spend day {d.day_number} immersed in {clean_dest}'s premier attractions, including {stop_names}. "
                    f"Enjoy relaxed transit and immersive cultural sightseeing."
                )
                stop_notes = {s.place_id: f"Take time to explore {s.name} and appreciate the surrounding atmosphere." for s in d.stops}
            else:
                theme_title = f"Day {d.day_number}: Leisure & Local Discovery in {clean_dest}"
                description = f"Free day to explore local markets, cafes, and neighborhoods at your own leisure."
                stop_notes = {}

            day_narratives.append(
                {
                    "day_number": d.day_number,
                    "theme_title": theme_title,
                    "description": description,
                    "stop_notes": stop_notes,
                }
            )

        practical_tips = [
            f"Carry a government-issued photo ID when visiting major attractions across {clean_dest}.",
            "Stay well-hydrated and verify local operational hours before setting out.",
            "Pre-arrange taxi or rideshare transportation during morning and evening rush hours.",
        ]

        return {
            "trip_title": trip_title,
            "trip_summary": trip_summary,
            "day_narratives": day_narratives,
            "practical_tips": practical_tips,
        }

    def _enrich_with_gemini(
        self,
        destination: str,
        departure_city: Optional[str],
        duration_days: int,
        pace: str,
        interests: List[str],
        hotel: Optional[HotelBookingRecommendation],
        outbound: Optional[FlightBookingRecommendation],
        days: List[ItineraryDay],
    ) -> Dict[str, Any]:
        """Invoke Gemini to generate creative narratives for pre-scheduled stops."""
        if not self.enable_gemini or self.client is None:
            return self._generate_deterministic_narrative(destination, days, pace, interests)

        gemini_input = {
            "destination": destination,
            "departure_city": departure_city,
            "duration_days": duration_days,
            "pace": pace,
            "interests": interests,
            "selected_hotel": hotel.name if hotel else None,
            "selected_outbound_flight": f"{outbound.carrier} ({outbound.origin_iata} to {outbound.destination_iata})" if outbound else None,
            "days": [
                {
                    "day_number": d.day_number,
                    "date": d.date,
                    "stops": [
                        {
                            "place_id": s.place_id,
                            "name": s.name,
                            "category": s.category,
                            "time_slot": s.time_slot,
                        }
                        for s in d.stops
                    ],
                }
                for d in days
            ],
        }

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
            system_instruction=ITINERARY_SYSTEM_PROMPT,
        )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as gemini_executor:
                future = gemini_executor.submit(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=json.dumps(gemini_input, indent=2),
                    config=config,
                )
                response = future.result(timeout=7.0)

            if not response or not response.text:
                raise ValueError("Empty response text from Gemini.")

            clean_text = self._clean_json_text(response.text)
            parsed = json.loads(clean_text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed Gemini output is not a JSON object.")

            return parsed
        except Exception as exc:
            logger.warning("Gemini narrative enrichment failed (%s); using deterministic fallback.", exc)
            return self._generate_deterministic_narrative(destination, days, pace, interests)

    def synthesize_itinerary(
        self,
        request: TripAggregationRequest,
        aggregation_result: Optional[TripAggregationResult] = None,
    ) -> TripItinerary:
        """Synthesize a complete TripItinerary from request and candidate aggregation data."""
        aggregator = self._get_aggregator()

        if aggregation_result is None:
            aggregation_result = aggregator.aggregate_trip(request)

        duration_days = aggregation_result.duration_days
        pace = request.pace

        # Step 1: Select flight candidates
        selected_outbound, selected_return = self._select_flights(
            outbound_flights=aggregation_result.outbound_flights,
            return_flights=aggregation_result.return_flights,
            is_same_day=aggregation_result.is_same_day,
        )

        # Step 2: Select hotel candidate
        selected_hotel = self._select_hotel(
            hotels=aggregation_result.hotels,
            is_same_day=aggregation_result.is_same_day,
        )

        # Step 3: Pure Python day-wise scheduling & travel calculation
        scheduled_days = self._schedule_days(
            places=aggregation_result.places,
            duration_days=duration_days,
            start_date=request.start_date,
            pace=pace,
            interests=request.interests,
            matrix=aggregation_result.places_distance_matrix,
        )

        # Step 4: Gemini narrative enrichment (with deterministic fallback)
        narrative_data = self._enrich_with_gemini(
            destination=request.destination,
            departure_city=request.departure_city,
            duration_days=duration_days,
            pace=pace,
            interests=request.interests,
            hotel=selected_hotel,
            outbound=selected_outbound,
            days=scheduled_days,
        )

        # Step 5: Merge narrative enrichment into locked-down schedule
        trip_title = narrative_data.get("trip_title") or f"{duration_days}-Day Trip to {request.destination.title()}"
        trip_summary = narrative_data.get("trip_summary") or f"A memorable journey through {request.destination.title()}."
        practical_tips = narrative_data.get("practical_tips") or [
            "Check local opening times and book tickets in advance where available.",
            "Keep digital copies of all reservations and IDs on your mobile device.",
        ]

        # Map day narratives and stop notes strictly by existing place_ids
        day_narratives_list = narrative_data.get("day_narratives", [])
        narrative_by_day = {}
        if isinstance(day_narratives_list, list):
            for dn in day_narratives_list:
                if isinstance(dn, dict) and "day_number" in dn:
                    narrative_by_day[dn["day_number"]] = dn

        for day in scheduled_days:
            dn = narrative_by_day.get(day.day_number)
            if dn:
                if dn.get("theme_title"):
                    day.theme_title = str(dn["theme_title"]).strip()
                if dn.get("description"):
                    day.day_description = str(dn["description"]).strip()

                stop_notes_map = dn.get("stop_notes") or {}
                if isinstance(stop_notes_map, dict):
                    for stop in day.stops:
                        # Only take note if the place_id matches an actual pre-scheduled stop
                        if stop.place_id in stop_notes_map:
                            stop.activity_notes = str(stop_notes_map[stop.place_id]).strip()
                        elif not stop.activity_notes:
                            stop.activity_notes = f"Visit and explore {stop.name}."
            else:
                for stop in day.stops:
                    if not stop.activity_notes:
                        stop.activity_notes = f"Visit and explore {stop.name}."

        # Step 6: Cost calculation
        flights_cost: Optional[float] = None
        accommodation_cost: Optional[float] = None

        if request.departure_city:
            if aggregation_result.is_same_day:
                if selected_outbound:
                    flights_cost = selected_outbound.price_amount + (
                        selected_return.price_amount if selected_return else 0.0
                    )
            else:
                if selected_outbound and selected_return:
                    flights_cost = selected_outbound.price_amount + selected_return.price_amount
                elif selected_outbound:
                    flights_cost = selected_outbound.price_amount
        else:
            flights_cost = None

        if aggregation_result.is_same_day:
            accommodation_cost = 0.0
        elif selected_hotel:
            accommodation_cost = selected_hotel.total_price
        else:
            accommodation_cost = None

        total_stops_count = sum(len(d.stops) for d in scheduled_days)
        estimated_activities_cost = 500.0 * total_stops_count

        # Check if cost estimation is complete
        is_cost_complete = True
        if request.departure_city and flights_cost is None:
            is_cost_complete = False
        if not aggregation_result.is_same_day and accommodation_cost is None:
            is_cost_complete = False

        if is_cost_complete:
            flight_part = flights_cost if flights_cost is not None else 0.0
            hotel_part = accommodation_cost if accommodation_cost is not None else 0.0
            total_estimated_cost: Optional[float] = round(flight_part + hotel_part + estimated_activities_cost, 2)
            is_within_budget: Optional[bool] = (
                total_estimated_cost <= request.budget if request.budget is not None else None
            )
        else:
            total_estimated_cost = None
            is_within_budget = None

        cost_breakdown = CostBreakdown(
            flights_cost=flights_cost,
            accommodation_cost=accommodation_cost,
            estimated_activities_cost=estimated_activities_cost,
            total_estimated_cost=total_estimated_cost,
            currency=request.currency,
            budget=request.budget,
            is_within_budget=is_within_budget,
            is_cost_complete=is_cost_complete,
        )

        return TripItinerary(
            trip_title=trip_title,
            destination=request.destination,
            departure_city=request.departure_city,
            start_date=request.start_date,
            end_date=request.end_date,
            duration_days=duration_days,
            is_same_day=aggregation_result.is_same_day,
            pace=pace,
            trip_summary=trip_summary,
            selected_outbound_flight=selected_outbound,
            selected_return_flight=selected_return,
            selected_hotel=selected_hotel,
            candidate_outbound_flights=aggregation_result.outbound_flights if aggregation_result else [],
            candidate_return_flights=aggregation_result.return_flights if aggregation_result else [],
            candidate_hotels=aggregation_result.hotels if aggregation_result else [],
            days=scheduled_days,
            cost_breakdown=cost_breakdown,
            practical_tips=practical_tips,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _recompute_day_transit(self, day: ItineraryDay) -> ItineraryDay:
        """Re-index stop numbers, assign time slots, and recalculate travel metrics between stops."""
        num_stops = len(day.stops)
        if num_stops == 0:
            day.total_travel_minutes = 0.0
            day.total_travel_km = 0.0
            return day

        time_slots = TIME_SLOT_TEMPLATES.get(num_stops)
        if not time_slots:
            time_slots = [f"{9 + i * 2}:00 - {11 + i * 2}:00" for i in range(num_stops)]

        day_travel_mins = 0.0
        day_travel_km = 0.0

        for k in range(num_stops):
            stop = day.stops[k]
            stop.stop_number = k + 1
            stop.time_slot = time_slots[k] if k < len(time_slots) else "15:00 - 17:00"
            stop.duration_minutes = 90 if k >= 3 else 120

            if k == 0:
                stop.travel_from_previous_minutes = 0.0
                stop.travel_from_previous_km = 0.0
                stop.routing_provider = "osrm"
                stop.is_estimated_travel = False
            else:
                prev_stop = day.stops[k - 1]
                trav_mins, trav_km, provider, is_est = self._get_travel_between(
                    place_a=Place(
                        place_id=prev_stop.place_id,
                        name=prev_stop.name,
                        category=prev_stop.category,
                        latitude=prev_stop.latitude,
                        longitude=prev_stop.longitude,
                        source_provider="osm",
                    ),
                    place_b=Place(
                        place_id=stop.place_id,
                        name=stop.name,
                        category=stop.category,
                        latitude=stop.latitude,
                        longitude=stop.longitude,
                        source_provider="osm",
                    ),
                    matrix=None,
                )
                stop.travel_from_previous_minutes = trav_mins
                stop.travel_from_previous_km = trav_km
                stop.routing_provider = provider
                stop.is_estimated_travel = is_est

            day_travel_mins += stop.travel_from_previous_minutes
            day_travel_km += stop.travel_from_previous_km

        day.total_travel_minutes = round(day_travel_mins, 1)
        day.total_travel_km = round(day_travel_km, 2)
        return day

    def replan_itinerary(self, request: ItineraryReplanRequest) -> TripItinerary:
        """Dynamically update an existing TripItinerary with stop additions, removals, reorders, or pace changes."""
        itinerary = request.current_itinerary.model_copy(deep=True)
        days_map: Dict[int, ItineraryDay] = {d.day_number: d for d in itinerary.days}
        existing_place_ids = {s.place_id for d in itinerary.days for s in d.stops}
        affected_days = set()

        # 1. Remove stops
        if request.remove_place_ids:
            remove_set = set(request.remove_place_ids)
            for d in itinerary.days:
                initial_count = len(d.stops)
                d.stops = [s for s in d.stops if s.place_id not in remove_set]
                if len(d.stops) != initial_count:
                    affected_days.add(d.day_number)
            existing_place_ids -= remove_set

        # 2. Reorder stops within a day
        if request.reorder_days:
            for day_num, ordered_ids in request.reorder_days.items():
                if day_num not in days_map:
                    raise ValueError(f"Invalid day_number {day_num} in reorder_days.")
                target_day = days_map[day_num]
                current_pids = {s.place_id for s in target_day.stops}
                if set(ordered_ids) != current_pids:
                    raise ValueError(
                        f"Reorder list for Day {day_num} must contain the exact same place IDs currently on that day."
                    )
                if len(ordered_ids) != len(set(ordered_ids)):
                    raise ValueError(f"Duplicate place IDs specified in reorder list for Day {day_num}.")
                stop_lookup = {s.place_id: s for s in target_day.stops}
                target_day.stops = [stop_lookup[pid] for pid in ordered_ids]
                affected_days.add(day_num)

        # 3. Add stops
        if request.add_stops:
            for action in request.add_stops:
                day_num = action.day_number
                if day_num not in days_map:
                    raise ValueError(f"Cannot add stop: Day {day_num} does not exist in itinerary.")
                target_day = days_map[day_num]
                if len(target_day.stops) >= 5:
                    raise ValueError(f"Cannot add stop: Day {day_num} already has the maximum of 5 stops.")

                place = action.place
                if not place.place_id or not place.name:
                    raise ValueError("Added stop must have a valid place_id and name.")
                if place.latitude is None or place.longitude is None:
                    raise ValueError(f"Added stop '{place.name}' must have valid coordinates.")
                if place.place_id in existing_place_ids:
                    raise ValueError(f"Place '{place.name}' ({place.place_id}) is already in the itinerary.")

                new_stop = ItineraryStop(
                    stop_number=len(target_day.stops) + 1,
                    place_id=place.place_id,
                    name=place.name,
                    category=place.category or "tourism.sights",
                    latitude=place.latitude,
                    longitude=place.longitude,
                    address=place.address,
                    image_url=place.image_url,
                    time_slot="15:00 - 17:00",
                    duration_minutes=90,
                    travel_from_previous_minutes=0.0,
                    travel_from_previous_km=0.0,
                    routing_provider="osrm",
                    is_estimated_travel=False,
                    activity_notes=f"Explore {place.name}.",
                )

                pos = action.position
                if pos is not None and 1 <= pos <= len(target_day.stops):
                    target_day.stops.insert(pos - 1, new_stop)
                else:
                    target_day.stops.append(new_stop)

                existing_place_ids.add(place.place_id)
                affected_days.add(day_num)

        # 4. Pace or Interests update
        if request.new_pace or request.new_interests:
            new_pace = request.new_pace or itinerary.pace
            itinerary.pace = new_pace
            interests = request.new_interests if request.new_interests is not None else []

            pool_places = []
            seen_pool = set()
            for d in itinerary.days:
                for s in d.stops:
                    if s.place_id not in seen_pool:
                        seen_pool.add(s.place_id)
                        pool_places.append(
                            Place(
                                place_id=s.place_id,
                                name=s.name,
                                category=s.category,
                                latitude=s.latitude,
                                longitude=s.longitude,
                                address=s.address,
                                image_url=s.image_url,
                                source_provider="existing",
                            )
                        )
            if request.candidate_places:
                for p in request.candidate_places:
                    if p.place_id not in seen_pool:
                        seen_pool.add(p.place_id)
                        pool_places.append(p)

            recomputed_days = self._schedule_days(
                places=pool_places,
                duration_days=itinerary.duration_days,
                start_date=itinerary.start_date,
                pace=new_pace,
                interests=interests,
                matrix=None,
            )
            itinerary.days = recomputed_days
            affected_days = {d.day_number for d in itinerary.days}
            days_map = {d.day_number: d for d in itinerary.days}

        # 5. Recalculate routes and schedule for all days
        for d in itinerary.days:
            if len(d.stops) == 0:
                d.theme_title = f"Day {d.day_number}: Leisure & Exploration in {itinerary.destination.title()}"
                d.day_description = "Free day to relax and explore local neighborhoods, markets, and culinary spots at your own pace."
                d.total_travel_minutes = 0.0
                d.total_travel_km = 0.0
            else:
                self._recompute_day_transit(d)
                if d.day_number in affected_days:
                    d.theme_title = f"Day {d.day_number}: Highlights around {d.stops[0].name}"
                    stop_names = ", ".join(s.name for s in d.stops[:3])
                    d.day_description = f"Spend day {d.day_number} exploring {itinerary.destination.title()}'s attractions, including {stop_names}."

        # 6. Narrative update (via Gemini if enabled, else deterministic update)
        if self.enable_gemini and self.client:
            try:
                narrative_data = self._enrich_with_gemini(
                    destination=itinerary.destination,
                    departure_city=itinerary.departure_city,
                    duration_days=itinerary.duration_days,
                    pace=itinerary.pace,
                    interests=request.new_interests or [],
                    hotel=itinerary.selected_hotel,
                    outbound=itinerary.selected_outbound_flight,
                    days=itinerary.days,
                )
                if narrative_data.get("trip_title"):
                    itinerary.trip_title = str(narrative_data["trip_title"]).strip()
                if narrative_data.get("trip_summary"):
                    itinerary.trip_summary = str(narrative_data["trip_summary"]).strip()
                if narrative_data.get("practical_tips"):
                    itinerary.practical_tips = [str(t).strip() for t in narrative_data["practical_tips"]]

                dn_list = narrative_data.get("day_narratives", [])
                if isinstance(dn_list, list):
                    dn_by_day = {dn["day_number"]: dn for dn in dn_list if isinstance(dn, dict) and "day_number" in dn}
                    for d in itinerary.days:
                        dn = dn_by_day.get(d.day_number)
                        if dn:
                            if dn.get("theme_title"):
                                d.theme_title = str(dn["theme_title"]).strip()
                            if dn.get("description"):
                                d.day_description = str(dn["description"]).strip()
                            stop_notes = dn.get("stop_notes") or {}
                            if isinstance(stop_notes, dict):
                                for s in d.stops:
                                    if s.place_id in stop_notes:
                                        s.activity_notes = str(stop_notes[s.place_id]).strip()
            except Exception as exc:
                logger.warning("Gemini replan narrative enrichment failed: %s; using deterministic narrative.", exc)
                itinerary.trip_title = f"{itinerary.duration_days}-Day {itinerary.destination.title()} Explorer ({itinerary.pace.title()})"
                itinerary.trip_summary = f"An updated {itinerary.pace} {itinerary.duration_days}-day itinerary across {itinerary.destination.title()}."
        else:
            itinerary.trip_title = f"{itinerary.duration_days}-Day {itinerary.destination.title()} Explorer ({itinerary.pace.title()})"
            itinerary.trip_summary = f"An updated {itinerary.pace} {itinerary.duration_days}-day itinerary across {itinerary.destination.title()}."

        # 7. Update Cost Breakdown
        total_stops_count = sum(len(d.stops) for d in itinerary.days)
        estimated_activities_cost = 500.0 * total_stops_count

        cb = itinerary.cost_breakdown
        is_cost_complete = cb.is_cost_complete
        if is_cost_complete:
            f_cost = cb.flights_cost if cb.flights_cost is not None else 0.0
            h_cost = cb.accommodation_cost if cb.accommodation_cost is not None else 0.0
            total_estimated_cost = round(f_cost + h_cost + estimated_activities_cost, 2)
            is_within_budget = (total_estimated_cost <= cb.budget) if cb.budget is not None else None
        else:
            total_estimated_cost = None
            is_within_budget = None

        itinerary.cost_breakdown.estimated_activities_cost = estimated_activities_cost
        itinerary.cost_breakdown.total_estimated_cost = total_estimated_cost
        itinerary.cost_breakdown.is_within_budget = is_within_budget
        itinerary.cost_breakdown.is_cost_complete = is_cost_complete
        itinerary.generated_at = datetime.now(timezone.utc).isoformat()

        return itinerary


_synthesizer_instance: Optional[ItinerarySynthesizer] = None


def get_itinerary_synthesizer() -> ItinerarySynthesizer:
    """Singleton provider for ItinerarySynthesizer."""
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = ItinerarySynthesizer()
    return _synthesizer_instance

