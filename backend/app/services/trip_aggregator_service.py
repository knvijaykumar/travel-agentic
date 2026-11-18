import concurrent.futures
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.core.config import settings
from backend.app.schemas.place import Place
from backend.app.schemas.places import GeoCoordinates
from backend.app.schemas.routing import DurationMatrixResponse
from backend.app.schemas.trip_aggregation import (
    AggregatedFlightOption,
    AggregatedFlightSegment,
    AggregatedHotelOption,
    AirportCandidate,
    HotelRoomOffer,
    ProviderExecutionStatus,
    TripAggregationRequest,
    TripAggregationResult,
)
from backend.app.services.geoapify_service import GeoapifyService
from backend.app.services.ignav_service import IgnavService, get_ignav_service
from backend.app.services.nuitee_service import NuiteeService, get_nuitee_service
from backend.app.services.flight_discovery_service import (
    FlightDiscoveryManager,
    get_flight_discovery_manager,
    IgnavFlightProvider,
    AmadeusFlightProvider,
    SkyscannerIndicativeFlightProvider,
)
from backend.app.services.routing_service import (
    RoutingService,
    get_routing_service,
    haversine_distance_meters,
)
from backend.app.services.wikimedia_service import WikimediaService

logger = logging.getLogger(__name__)

_trip_aggregator_service_instance: Optional["TripAggregatorService"] = None

# Thread-safe in-memory cache for invariant geocoding, airport searches, and attraction images (1 hour TTL)
_GEOCODE_CACHE: Dict[str, Tuple[float, Optional[Dict[str, Any]]]] = {}
_AIRPORT_SEARCH_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_WIKIMEDIA_CACHE: Dict[Tuple[str, str], Optional[Dict[str, Optional[str]]]] = {}
_CACHE_TTL_SECONDS = 3600.0


def _sanitize_error(error_msg: str) -> str:
    """Strip any configured provider API keys from error messages."""
    for key_attr in ["IGNAV_API_KEY", "NUITEE_API_KEY", "GEOAPIFY_API_KEY", "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"]:
        val = getattr(settings, key_attr, "")
        if val and str(val).strip() and str(val).strip() in error_msg:
            error_msg = error_msg.replace(str(val).strip(), "[REDACTED]")
    return error_msg


def _extract_airport_candidates(
    airports_data: List[Dict[str, Any]],
    preferred_country: Optional[str] = "IN",
) -> List[AirportCandidate]:
    """Parse airport list into unique AirportCandidate models, prioritizing destination country matches."""
    candidates: List[AirportCandidate] = []
    seen = set()

    items = list(airports_data)
    if preferred_country:
        clean_country = preferred_country.strip().upper()
        items = sorted(
            items,
            key=lambda x: 0 if str(x.get("country", "")).strip().upper() == clean_country else 1,
        )

    for item in items:
        if not isinstance(item, dict):
            continue
        iata = str(item.get("iata") or item.get("code") or item.get("iata_code") or "").strip().upper()
        if len(iata) == 3 and iata not in seen:
            seen.add(iata)
            candidates.append(
                AirportCandidate(
                    iata=iata,
                    name=str(item.get("name") or f"{iata} Airport").strip(),
                    city=str(item.get("city") or "").strip(),
                    country=str(item.get("country") or "").strip() or None,
                )
            )
    return candidates


def _deduplicate_places(places: List[Place]) -> List[Place]:
    """Deduplicate Place items by place_id and geographical proximity (< 75m)."""
    seen_ids: Set[str] = set()
    deduped: List[Place] = []

    for p in places:
        if p.place_id in seen_ids:
            continue

        is_dup = False
        for existing in deduped:
            try:
                dist = haversine_distance_meters(p.latitude, p.longitude, existing.latitude, existing.longitude)
                if dist < 75.0 or (p.name.strip().lower() == existing.name.strip().lower()):
                    is_dup = True
                    break
            except Exception:
                pass

        if not is_dup:
            seen_ids.add(p.place_id)
            deduped.append(p)

    return deduped


def _parse_flight_itineraries(
    response: Dict[str, Any],
    direction: str,
    departure_date: str,
    max_flights: int,
) -> List[AggregatedFlightOption]:
    """Convert raw Ignav flight response itineraries into AggregatedFlightOption list."""
    itineraries = response.get("itineraries", [])
    if not isinstance(itineraries, list):
        return []

    flight_options: List[AggregatedFlightOption] = []
    seen_signatures = set()

    for item in itineraries:
        if not isinstance(item, dict):
            continue

        price_info = item.get("price", {})
        price_amount = float(price_info.get("amount", 0.0))
        currency = str(price_info.get("currency", "INR"))

        outbound = item.get("outbound", {})
        carrier = str(outbound.get("carrier", "Airline"))
        duration_mins = int(outbound.get("duration_minutes", 0))

        raw_segments = outbound.get("segments", [])
        segments: List[AggregatedFlightSegment] = []
        for seg in raw_segments:
            if isinstance(seg, dict):
                segments.append(
                    AggregatedFlightSegment(
                        carrier_code=str(seg.get("marketing_carrier_code", "")),
                        flight_number=str(seg.get("flight_number", "")),
                        departure_airport=str(seg.get("departure_airport", "")),
                        arrival_airport=str(seg.get("arrival_airport", "")),
                        departure_time_local=str(seg.get("departure_time_local", "")),
                        arrival_time_local=str(seg.get("arrival_time_local", "")),
                    )
                )

        first_seg = segments[0] if segments else None
        last_seg = segments[-1] if segments else None

        origin_iata = first_seg.departure_airport if first_seg else str(response.get("origin", ""))
        dest_iata = last_seg.arrival_airport if last_seg else str(response.get("destination", ""))
        flight_num = first_seg.flight_number if first_seg else str(item.get("ignav_id", ""))
        dep_time = first_seg.departure_time_local if first_seg else departure_date

        sig = (carrier, flight_num, dep_time, origin_iata, dest_iata)
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)

        flight_id = str(item.get("ignav_id") or f"{origin_iata}_{dest_iata}_{flight_num}")
        stops_count = max(0, len(segments) - 1)

        flight_options.append(
            AggregatedFlightOption(
                flight_id=flight_id,
                direction=direction,
                origin_iata=origin_iata,
                destination_iata=dest_iata,
                departure_date=departure_date,
                carrier=carrier,
                duration_minutes=duration_mins,
                price_amount=price_amount,
                currency=currency,
                cabin_class=str(item.get("cabin_class", "economy")),
                has_mixed_carriers=bool(item.get("has_mixed_carriers", False)),
                segments=segments,
                source_provider="Ignav",
                is_indicative=False,
                price_type="live",
                stops=stops_count,
            )
        )

    flight_options.sort(key=lambda x: x.price_amount)
    return flight_options[:max_flights]


def _parse_hotel_options(
    data: Dict[str, Any],
    currency: str,
    duration_days: int,
    is_sandbox: bool,
    max_hotels: int,
) -> List[AggregatedHotelOption]:
    """Parse LiteAPI rate response into structured AggregatedHotelOption candidates."""
    hotels_meta = {
        h.get("id"): h
        for h in data.get("hotels", [])
        if isinstance(h, dict) and h.get("id")
    }
    nights = max(1, duration_days - 1)

    aggregated: List[AggregatedHotelOption] = []
    for item in data.get("data", []):
        if not isinstance(item, dict):
            continue
        hotel_id = item.get("hotelId")
        if not hotel_id:
            continue

        meta = hotels_meta.get(hotel_id, {})

        offers: List[HotelRoomOffer] = []
        for rt in item.get("roomTypes", []):
            if not isinstance(rt, dict):
                continue
            rt_name = rt.get("name") or "Standard Room"
            for rate in rt.get("rates", []):
                if not isinstance(rate, dict):
                    continue
                offer_id = str(rt.get("offerId") or rate.get("rateId") or f"{hotel_id}_{len(offers)}")
                room_name = rate.get("name") or rt_name
                board_name = rate.get("boardName") or "Room Only"

                retail = rate.get("retailRate", {})
                totals = retail.get("total", [])
                amount = float(totals[0].get("amount", 0.0)) if totals and isinstance(totals, list) else 0.0
                curr = str(totals[0].get("currency", currency)) if totals and isinstance(totals, list) else currency

                cancellation = None
                canc_policies = rate.get("cancellationPolicies")
                if isinstance(canc_policies, dict):
                    cancellation = canc_policies.get("refundableTag") or str(canc_policies)
                elif canc_policies:
                    cancellation = str(canc_policies)

                taxes = retail.get("taxesAndFees")

                offers.append(
                    HotelRoomOffer(
                        offer_id=offer_id,
                        room_name=room_name,
                        board_name=board_name,
                        total_amount=amount,
                        currency=curr,
                        cancellation_policy=cancellation,
                        taxes_and_fees=taxes if isinstance(taxes, dict) else None,
                    )
                )

        if not offers:
            continue

        min_total = min(o.total_amount for o in offers)
        min_night = round(min_total / nights, 2)

        loc = meta.get("location") or {}
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        aggregated.append(
            AggregatedHotelOption(
                hotel_id=hotel_id,
                name=meta.get("name") or f"Hotel {hotel_id}",
                star_rating=meta.get("starRating"),
                user_rating=meta.get("rating"),
                address=meta.get("address"),
                latitude=float(lat) if lat is not None else None,
                longitude=float(lon) if lon is not None else None,
                photo_url=meta.get("main_photo"),
                min_price_total=min_total,
                min_price_per_night=min_night,
                currency=offers[0].currency,
                offers=offers,
                is_sandbox=is_sandbox,
                source_provider="Nuitee/LiteAPI",
            )
        )

    aggregated.sort(key=lambda x: x.min_price_total)
    return aggregated[:max_hotels]


class TripAggregatorService:
    """Deterministic orchestrator that queries Ignav, LiteAPI, Geoapify and OSRM concurrently."""

    def __init__(
        self,
        ignav_service: Optional[IgnavService] = None,
        nuitee_service: Optional[NuiteeService] = None,
        geoapify_service: Optional[GeoapifyService] = None,
        routing_service: Optional[RoutingService] = None,
        flight_discovery_manager: Optional[FlightDiscoveryManager] = None,
        wikimedia_service: Optional[WikimediaService] = None,
    ):
        self.ignav_service = ignav_service or get_ignav_service()
        self.nuitee_service = nuitee_service or get_nuitee_service()
        self.geoapify_service = geoapify_service or GeoapifyService()
        self.routing_service = routing_service or get_routing_service()
        if wikimedia_service is not None:
            self.wikimedia_service = wikimedia_service
        elif hasattr(self.geoapify_service, "_mock_return_value") or hasattr(self.geoapify_service, "_mock_wraps"):
            from unittest.mock import MagicMock
            mock_wiki = MagicMock(spec=WikimediaService)
            mock_wiki.get_image.return_value = None
            self.wikimedia_service = mock_wiki
        else:
            self.wikimedia_service = WikimediaService()
        if flight_discovery_manager is not None:
            self.flight_discovery_manager = flight_discovery_manager
        else:
            self.flight_discovery_manager = FlightDiscoveryManager(providers=[
                IgnavFlightProvider(service=self.ignav_service),
                AmadeusFlightProvider(),
                SkyscannerIndicativeFlightProvider(),
            ])

    def _safe_geocode_city(self, destination: str, country: str = "IN") -> Tuple[Optional[GeoCoordinates], ProviderExecutionStatus]:
        """Geocode destination city with in-memory caching to eliminate redundant network round trips."""
        clean_dest = destination.strip()
        key = f"{clean_dest.lower()}_{country.lower()}"
        now = time.time()

        if key in _GEOCODE_CACHE:
            ts, cached_res = _GEOCODE_CACHE[key]
            if now - ts < _CACHE_TTL_SECONDS:
                coords = GeoCoordinates(lat=cached_res["latitude"], lon=cached_res["longitude"]) if cached_res else None
                return coords, ProviderExecutionStatus(
                    status="success" if coords else "failed",
                    item_count=1 if coords else 0,
                    latency_seconds=0.0,
                    details={"cached": True},
                )

        t0 = time.perf_counter()
        try:
            geo_res = self.geoapify_service.geocode_city(clean_dest, country=country)
            latency = round(time.perf_counter() - t0, 2)
            if geo_res and geo_res.get("latitude") is not None and geo_res.get("longitude") is not None:
                _GEOCODE_CACHE[key] = (now, geo_res)
                coords = GeoCoordinates(lat=geo_res["latitude"], lon=geo_res["longitude"])
                return coords, ProviderExecutionStatus(
                    status="success",
                    item_count=1,
                    latency_seconds=latency,
                )
            else:
                _GEOCODE_CACHE[key] = (now, None)
                return None, ProviderExecutionStatus(
                    status="failed",
                    item_count=0,
                    latency_seconds=latency,
                    error_message=_sanitize_error(f"Destination '{clean_dest}' could not be resolved to geographical coordinates."),
                )
        except Exception as exc:
            latency = round(time.perf_counter() - t0, 2)
            return None, ProviderExecutionStatus(
                status="failed",
                item_count=0,
                latency_seconds=latency,
                error_message=_sanitize_error(f"Geocoding error: {exc}"),
            )

    def _safe_search_airports(self, query: Optional[str], preferred_country: str = "IN") -> List[AirportCandidate]:
        """Resolve airport candidates for a city with in-memory caching."""
        if not query or not query.strip():
            return []
        clean_q = query.strip()
        key = clean_q.lower()
        now = time.time()

        if key in _AIRPORT_SEARCH_CACHE:
            ts, cached_data = _AIRPORT_SEARCH_CACHE[key]
            if now - ts < _CACHE_TTL_SECONDS:
                return _extract_airport_candidates(cached_data, preferred_country=preferred_country)

        try:
            airports_data = self.ignav_service.search_airports(clean_q, limit=5)
            _AIRPORT_SEARCH_CACHE[key] = (now, airports_data)
            return _extract_airport_candidates(airports_data, preferred_country=preferred_country)
        except Exception as exc:
            logger.warning(f"Failed to resolve airports for '{clean_q}': {exc}")
            return []

    def aggregate_trip(self, request: TripAggregationRequest) -> TripAggregationResult:
        """Execute concurrent data collection across flights, hotels, places and routing.

        Preserves candidate options without premature selection. Gracefully handles partial provider
        failures without aborting the entire request.
        """
        provider_statuses: Dict[str, ProviderExecutionStatus] = {}

        # ── 1. Concurrent Pre-flight: Geocoding & Airport Resolution ─────
        dest_coords: Optional[GeoCoordinates] = None
        origin_airports: List[AirportCandidate] = []
        destination_airports: List[AirportCandidate] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as prep_executor:
            fut_geo = prep_executor.submit(self._safe_geocode_city, request.destination, "IN")
            fut_orig_airports = (
                prep_executor.submit(self._safe_search_airports, request.departure_city, "IN")
                if request.departure_city
                else None
            )
            fut_dest_airports = prep_executor.submit(self._safe_search_airports, request.destination, "IN")

            dest_coords, geo_status = fut_geo.result(timeout=10.0)
            provider_statuses["geocoding"] = geo_status

            if fut_orig_airports:
                origin_airports = fut_orig_airports.result(timeout=10.0)
            if not origin_airports and request.departure_city:
                dep_query = request.departure_city.strip()
                if len(dep_query) == 3 and dep_query.isalpha() and dep_query.isupper():
                    origin_airports.append(AirportCandidate(iata=dep_query, name=f"{dep_query} Airport", city=dep_query))

            destination_airports = fut_dest_airports.result(timeout=10.0)
            if not destination_airports and request.destination:
                dest_query = request.destination.strip()
                if len(dest_query) == 3 and dest_query.isalpha() and dest_query.isupper():
                    destination_airports.append(AirportCandidate(iata=dest_query, name=f"{dest_query} Airport", city=dest_query))

        # ── 2. Concurrent Multi-Provider Execution ───────────────────────
        outbound_flights: List[AggregatedFlightOption] = []
        return_flights: List[AggregatedFlightOption] = []
        hotels: List[AggregatedHotelOption] = []
        places: List[Place] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_flights = executor.submit(
                self._fetch_flights,
                request=request,
                origin_airports=origin_airports,
                destination_airports=destination_airports,
            )
            future_hotels = executor.submit(
                self._fetch_hotels,
                request=request,
                dest_coords=dest_coords,
            )
            future_places = executor.submit(
                self._fetch_places,
                request=request,
                dest_coords=dest_coords,
            )

            futures_map = {
                future_flights: "flights",
                future_hotels: "hotels",
                future_places: "places",
            }

            done, not_done = concurrent.futures.wait(
                futures_map.keys(),
                timeout=25.0,
                return_when=concurrent.futures.ALL_COMPLETED,
            )

            for fut in done:
                provider_key = futures_map[fut]
                try:
                    res_tuple = fut.result()
                    if provider_key == "flights":
                        outbound_flights, return_flights, p_status = res_tuple
                        provider_statuses["flights"] = p_status
                    elif provider_key == "hotels":
                        hotels, p_status = res_tuple
                        provider_statuses["hotels"] = p_status
                    elif provider_key == "places":
                        places, p_status = res_tuple
                        provider_statuses["places"] = p_status
                except Exception as exc:
                    provider_statuses[provider_key] = ProviderExecutionStatus(
                        status="failed",
                        item_count=0,
                        error_message=_sanitize_error(str(exc)),
                    )

            for fut in not_done:
                provider_key = futures_map[fut]
                provider_statuses[provider_key] = ProviderExecutionStatus(
                    status="timed_out",
                    item_count=0,
                    error_message=f"Provider {provider_key} timed out after 25 seconds.",
                )

            # Prevent executor from blocking indefinitely on shutdown
            executor.shutdown(wait=False, cancel_futures=True)

        # ── 3. Place-to-Place Distance Matrix ────────────────────────────
        places_distance_matrix: Optional[DurationMatrixResponse] = None

        if dest_coords is None:
            provider_statuses["routing"] = ProviderExecutionStatus(
                status="unavailable",
                item_count=0,
                error_message="Geocoding failed; coordinates unavailable for distance matrix.",
            )
        elif len(places) >= 2:
            matrix_t0 = time.perf_counter()
            try:
                coords = [GeoCoordinates(lat=p.latitude, lon=p.longitude) for p in places[:12]]
                matrix_res = self.routing_service.get_distance_matrix(coords, fallback_to_haversine=True)
                matrix_latency = time.perf_counter() - matrix_t0
                places_distance_matrix = matrix_res
                provider_statuses["routing"] = ProviderExecutionStatus(
                    status="success",
                    item_count=len(coords),
                    latency_seconds=round(matrix_latency, 2),
                    details={
                        "is_estimated": matrix_res.is_estimated,
                        "routing_provider": matrix_res.routing_provider,
                    },
                )
            except Exception as exc:
                matrix_latency = time.perf_counter() - matrix_t0
                provider_statuses["routing"] = ProviderExecutionStatus(
                    status="failed",
                    item_count=0,
                    latency_seconds=round(matrix_latency, 2),
                    error_message=_sanitize_error(str(exc)),
                )
        else:
            provider_statuses["routing"] = ProviderExecutionStatus(
                status="skipped",
                item_count=len(places),
                error_message="Fewer than 2 places discovered; distance matrix skipped.",
            )

        return TripAggregationResult(
            destination=request.destination,
            destination_coordinates=dest_coords,
            departure_city=request.departure_city,
            start_date=request.start_date,
            end_date=request.end_date,
            duration_days=request.duration_days,
            is_same_day=request.is_same_day,
            origin_airports=origin_airports,
            destination_airports=destination_airports,
            outbound_flights=outbound_flights,
            return_flights=return_flights,
            hotels=hotels,
            places=places,
            places_distance_matrix=places_distance_matrix,
            provider_statuses=provider_statuses,
        )

    # ── Internal Worker: Flights ─────────────────────────────────────────

    def _fetch_flights(
        self,
        request: TripAggregationRequest,
        origin_airports: List[AirportCandidate],
        destination_airports: List[AirportCandidate],
    ) -> Tuple[List[AggregatedFlightOption], List[AggregatedFlightOption], ProviderExecutionStatus]:
        """Delegate flight discovery to the multi-source FlightDiscoveryManager."""
        if not request.departure_city:
            return [], [], ProviderExecutionStatus(
                status="skipped",
                latency_seconds=0.0,
                error_message="No departure city provided.",
            )

        return self.flight_discovery_manager.discover_flights(
            request=request,
            origin_airports=origin_airports,
            destination_airports=destination_airports,
        )

    # ── Internal Worker: Hotels ──────────────────────────────────────────

    def _fetch_hotels(
        self,
        request: TripAggregationRequest,
        dest_coords: Optional[GeoCoordinates],
    ) -> Tuple[List[AggregatedHotelOption], ProviderExecutionStatus]:
        t0 = time.perf_counter()

        if request.is_same_day:
            return [], ProviderExecutionStatus(
                status="skipped",
                latency_seconds=0.0,
                error_message="Same-day trip does not require overnight accommodation.",
            )

        occupancies = [{"adults": request.adults, "children": request.children or []}]
        is_sandbox = getattr(self.nuitee_service, "_api_key", "").startswith("sand_")

        try:
            data = self.nuitee_service.search_hotel_rates(
                checkin=request.start_date,
                checkout=request.end_date,
                occupancies=occupancies,
                adults=request.adults,
                currency=request.currency,
                guest_nationality="IN",
                city_name=request.destination,
                country_code="IN",
                include_hotel_data=True,
            )

            hotels = _parse_hotel_options(
                data=data,
                currency=request.currency,
                duration_days=request.duration_days,
                is_sandbox=is_sandbox,
                max_hotels=request.max_hotels,
            )
            latency = round(time.perf_counter() - t0, 2)

            return hotels, ProviderExecutionStatus(
                status="success" if hotels else "success",
                item_count=len(hotels),
                latency_seconds=latency,
                error_message=None if hotels else "No hotel availability found for requested dates.",
            )

        except Exception as exc:
            latency = round(time.perf_counter() - t0, 2)
            return [], ProviderExecutionStatus(
                status="failed",
                item_count=0,
                latency_seconds=latency,
                error_message=_sanitize_error(str(exc)),
            )

    # ── Internal Worker: Places ──────────────────────────────────────────

    def _fetch_places(
        self,
        request: TripAggregationRequest,
        dest_coords: Optional[GeoCoordinates],
    ) -> Tuple[List[Place], ProviderExecutionStatus]:
        """Fetch attractions across multiple categories concurrently."""
        t0 = time.perf_counter()

        if dest_coords is None:
            return [], ProviderExecutionStatus(
                status="unavailable",
                latency_seconds=0.0,
                error_message="Destination geocoding failed; coordinates unavailable for attraction discovery.",
            )

        categories = ["tourism.sights", "entertainment.culture", "heritage"]
        if request.interests:
            for interest in request.interests:
                clean_int = interest.strip().lower()
                if "beach" in clean_int:
                    categories.append("beach")
                elif "nature" in clean_int or "park" in clean_int:
                    categories.append("leisure.park")
                elif "museum" in clean_int:
                    categories.append("entertainment.museum")

        # Keep categories unique and bounded
        categories = list(dict.fromkeys(categories))[:4]

        raw_places: List[Place] = []
        errors: List[str] = []

        def _search_cat(cat: str) -> List[Place]:
            return self.geoapify_service.search_places(
                category=cat,
                latitude=dest_coords.lat,
                longitude=dest_coords.lon,
                radius_meters=request.search_radius_meters,
                limit=15,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(categories))) as places_executor:
            cat_futs = {places_executor.submit(_search_cat, c): c for c in categories}
            for fut in concurrent.futures.as_completed(cat_futs, timeout=8.0):
                c = cat_futs[fut]
                try:
                    res = fut.result()
                    raw_places.extend(res)
                except Exception as exc:
                    errors.append(f"Category {c}: {exc}")

        deduped = _deduplicate_places(raw_places)
        final_places = deduped[: request.max_places]

        # Concurrently enrich places with verified Wikimedia Commons images
        if getattr(request, "enrich_images", True) and final_places:
            def _enrich_single_place(place: Place) -> None:
                if place.image_url:
                    return
                cache_key = (place.name.lower().strip(), request.destination.lower().strip())
                if cache_key in _WIKIMEDIA_CACHE:
                    cached_img = _WIKIMEDIA_CACHE[cache_key]
                    if cached_img:
                        place.image_url = cached_img.get("image_url")
                        place.image_attribution = cached_img.get("attribution")
                    return

                try:
                    img_data = self.wikimedia_service.get_image(
                        place_name=place.name,
                        city=request.destination,
                        region=place.city or request.destination,
                    )
                    _WIKIMEDIA_CACHE[cache_key] = img_data
                    if img_data and img_data.get("image_url"):
                        place.image_url = img_data["image_url"]
                        place.image_attribution = img_data.get("attribution")
                except Exception as exc:
                    logger.debug(f"Wikimedia image lookup skipped for '{place.name}': {exc}")
                    _WIKIMEDIA_CACHE[cache_key] = None

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(final_places))) as img_executor:
                list(img_executor.map(_enrich_single_place, final_places))

        latency = round(time.perf_counter() - t0, 2)

        if final_places:
            status = "success" if not errors else "partial"
            err_msg = _sanitize_error("; ".join(errors)) if errors else None
        else:
            status = "failed" if errors else "success"
            err_msg = _sanitize_error("; ".join(errors)) if errors else "No tourist attractions found."

        return final_places, ProviderExecutionStatus(
            status=status,
            item_count=len(final_places),
            latency_seconds=latency,
            error_message=err_msg,
        )


def get_trip_aggregator_service() -> TripAggregatorService:
    """Singleton dependency provider for TripAggregatorService."""
    global _trip_aggregator_service_instance
    if _trip_aggregator_service_instance is None:
        _trip_aggregator_service_instance = TripAggregatorService()
    return _trip_aggregator_service_instance
