"""Multi-source flight discovery architecture with primary and secondary provider fallback."""

from abc import ABC, abstractmethod
import concurrent.futures
from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

from backend.app.core.config import settings
from backend.app.schemas.trip_aggregation import (
    AggregatedFlightOption,
    AggregatedFlightSegment,
    AirportCandidate,
    ProviderExecutionStatus,
    TripAggregationRequest,
)
from backend.app.services.ignav_service import IgnavService, get_ignav_service

logger = logging.getLogger(__name__)


def _sanitize_secrets(msg: str) -> str:
    """Sanitize any API keys or client secrets from error strings."""
    for attr in ["IGNAV_API_KEY", "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET", "SKYSCANNER_API_KEY"]:
        val = getattr(settings, attr, "") or os.getenv(attr, "")
        if val and str(val).strip() and str(val).strip() in msg:
            msg = msg.replace(str(val).strip(), "[REDACTED]")
    return msg


class BaseFlightProvider(ABC):
    """Abstract interface for a flight discovery provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider display name (e.g. 'Ignav', 'Amadeus', 'Skyscanner')."""
        pass

    @property
    @abstractmethod
    def is_indicative(self) -> bool:
        """Whether results from this provider are indicative estimates rather than live booking offers."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials and network configurations are available."""
        pass

    @abstractmethod
    def search_flights(
        self,
        request: TripAggregationRequest,
        origin_airports: List[AirportCandidate],
        destination_airports: List[AirportCandidate],
    ) -> Tuple[List[AggregatedFlightOption], List[AggregatedFlightOption], ProviderExecutionStatus]:
        """Search outbound and return flights between origin and destination airport candidates."""
        pass


class IgnavFlightProvider(BaseFlightProvider):
    """Primary live flight provider using Ignav Flight Prices API."""

    def __init__(self, service: Optional[IgnavService] = None):
        self.service = service or get_ignav_service()

    @property
    def name(self) -> str:
        return "Ignav"

    @property
    def is_indicative(self) -> bool:
        return False

    def is_available(self) -> bool:
        api_key = getattr(self.service, "_api_key", None)
        if isinstance(api_key, str):
            return bool(api_key.strip())
        if hasattr(self.service, "search_one_way_flights"):
            return True
        return False

    def search_flights(
        self,
        request: TripAggregationRequest,
        origin_airports: List[AirportCandidate],
        destination_airports: List[AirportCandidate],
    ) -> Tuple[List[AggregatedFlightOption], List[AggregatedFlightOption], ProviderExecutionStatus]:
        t0 = time.perf_counter()

        if not self.is_available():
            return [], [], ProviderExecutionStatus(
                status="unavailable",
                latency_seconds=0.0,
                error_message="IGNAV_API_KEY is not configured.",
            )

        if not origin_airports or not destination_airports:
            return [], [], ProviderExecutionStatus(
                status="skipped",
                latency_seconds=round(time.perf_counter() - t0, 2),
                error_message="Could not resolve commercial airport candidates for origin and/or destination.",
            )

        # Bounded airport combinations (top 2 origin x top 2 destination)
        pair_candidates = [
            (orig, dest)
            for orig in origin_airports[:2]
            for dest in destination_airports[:2]
            if orig.iata != dest.iata
        ]

        if not pair_candidates:
            return [], [], ProviderExecutionStatus(
                status="skipped",
                latency_seconds=round(time.perf_counter() - t0, 2),
                error_message="Origin and destination airport candidates are identical.",
            )

        all_outbound: List[AggregatedFlightOption] = []
        all_return: List[AggregatedFlightOption] = []
        errors: List[str] = []

        return_date = request.end_date if not request.is_same_day else request.start_date

        # Execute outbound and return searches concurrently across candidate pairs
        search_tasks: List[Tuple[str, str, str, str]] = []
        for orig, dest in pair_candidates:
            search_tasks.append((orig.iata, dest.iata, request.start_date, "outbound"))
            search_tasks.append((dest.iata, orig.iata, return_date, "return"))

        def _execute_search(orig_code: str, dest_code: str, dep_date: str, direction: str):
            res = self.service.search_one_way_flights(
                origin=orig_code,
                destination=dest_code,
                departure_date=dep_date,
                adults=request.adults,
                cabin_class="economy",
                market="IN",
            )
            return direction, dep_date, res

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(search_tasks))) as executor:
            future_to_task = {
                executor.submit(_execute_search, o, d, dt, dr): (o, d, dr)
                for (o, d, dt, dr) in search_tasks
            }

            for fut in concurrent.futures.as_completed(future_to_task, timeout=12.0):
                orig_code, dest_code, direction = future_to_task[fut]
                try:
                    dir_res, dep_date, raw_res = fut.result()
                    parsed = self._parse_itineraries(
                        raw_res,
                        direction=dir_res,
                        departure_date=dep_date,
                        max_flights=request.max_flights_per_leg,
                    )
                    if dir_res == "outbound":
                        all_outbound.extend(parsed)
                    else:
                        all_return.extend(parsed)
                except Exception as exc:
                    errors.append(f"{direction.capitalize()} {orig_code}->{dest_code}: {exc}")

        # Deduplicate and sort
        deduped_out = self._deduplicate_flights(all_outbound)
        deduped_ret = self._deduplicate_flights(all_return)

        latency = round(time.perf_counter() - t0, 2)
        total_found = len(deduped_out) + len(deduped_ret)

        if total_found > 0:
            status = "success" if not errors else "partial"
            err_msg = _sanitize_secrets("; ".join(errors)) if errors else None
        else:
            status = "failed" if errors else "success"
            err_msg = _sanitize_secrets("; ".join(errors)) if errors else "No flight itineraries returned."

        return (
            deduped_out[: request.max_flights_per_leg],
            deduped_ret[: request.max_flights_per_leg],
            ProviderExecutionStatus(
                status=status,
                item_count=total_found,
                latency_seconds=latency,
                error_message=err_msg,
            ),
        )

    def _parse_itineraries(
        self,
        response: Dict[str, Any],
        direction: str,
        departure_date: str,
        max_flights: int,
    ) -> List[AggregatedFlightOption]:
        itineraries = response.get("itineraries", [])
        if not isinstance(itineraries, list):
            return []

        flight_options: List[AggregatedFlightOption] = []
        seen_signatures = set()
        now_iso = datetime.now(timezone.utc).isoformat()

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
            raw_booking_url = item.get("booking_url") or item.get("deep_link") or item.get("url")

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
                    retrieved_at=now_iso,
                    booking_url=str(raw_booking_url).strip() if raw_booking_url else None,
                )
            )

        flight_options.sort(key=lambda x: x.price_amount)
        return flight_options[:max_flights]

    def _deduplicate_flights(self, flights: List[AggregatedFlightOption]) -> List[AggregatedFlightOption]:
        seen = set()
        deduped = []
        for f in flights:
            if f.flight_id not in seen:
                seen.add(f.flight_id)
                deduped.append(f)
        deduped.sort(key=lambda x: x.price_amount)
        return deduped


class AmadeusFlightProvider(BaseFlightProvider):
    """Secondary live flight provider using Amadeus Self-Service Flight Offers API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        hostname: Optional[str] = None,
    ):
        self.client_id = client_id or getattr(settings, "AMADEUS_CLIENT_ID", "") or os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or getattr(settings, "AMADEUS_CLIENT_SECRET", "") or os.getenv("AMADEUS_CLIENT_SECRET", "")
        self.hostname = (hostname or getattr(settings, "AMADEUS_HOSTNAME", "test.api.amadeus.com")).rstrip("/")

    @property
    def name(self) -> str:
        return "Amadeus"

    @property
    def is_indicative(self) -> bool:
        return False

    def is_available(self) -> bool:
        return bool(self.client_id.strip() and self.client_secret.strip())

    def _get_access_token(self) -> Optional[str]:
        if not self.is_available():
            return None
        token_url = f"https://{self.hostname}/v1/security/oauth2/token"
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }).encode("utf-8")
        req = urllib.request.Request(token_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("access_token")
        except Exception as exc:
            logger.warning(f"Amadeus OAuth2 token exchange failed: {exc}")
            return None

    def search_flights(
        self,
        request: TripAggregationRequest,
        origin_airports: List[AirportCandidate],
        destination_airports: List[AirportCandidate],
    ) -> Tuple[List[AggregatedFlightOption], List[AggregatedFlightOption], ProviderExecutionStatus]:
        t0 = time.perf_counter()

        if not self.is_available():
            return [], [], ProviderExecutionStatus(
                status="unavailable",
                latency_seconds=0.0,
                error_message="AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET not configured.",
            )

        token = self._get_access_token()
        if not token:
            return [], [], ProviderExecutionStatus(
                status="failed",
                latency_seconds=round(time.perf_counter() - t0, 2),
                error_message="Failed to obtain Amadeus OAuth2 bearer token.",
            )

        orig_iata = origin_airports[0].iata if origin_airports else "DEL"
        dest_iata = destination_airports[0].iata if destination_airports else "GOI"

        outbound_flights: List[AggregatedFlightOption] = []
        return_flights: List[AggregatedFlightOption] = []
        errors: List[str] = []

        # Query outbound
        try:
            params = {
                "originLocationCode": orig_iata,
                "destinationLocationCode": dest_iata,
                "departureDate": request.start_date,
                "adults": str(max(1, request.adults)),
                "currencyCode": request.currency,
                "max": str(request.max_flights_per_leg),
            }
            url = f"https://{self.hostname}/v2/shopping/flight-offers?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                outbound_flights = self._parse_amadeus_offers(data, "outbound", request.start_date, request.currency)
        except Exception as exc:
            errors.append(f"Amadeus outbound error: {exc}")

        # Query return
        return_date = request.end_date if not request.is_same_day else request.start_date
        try:
            params = {
                "originLocationCode": dest_iata,
                "destinationLocationCode": orig_iata,
                "departureDate": return_date,
                "adults": str(max(1, request.adults)),
                "currencyCode": request.currency,
                "max": str(request.max_flights_per_leg),
            }
            url = f"https://{self.hostname}/v2/shopping/flight-offers?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return_flights = self._parse_amadeus_offers(data, "return", return_date, request.currency)
        except Exception as exc:
            errors.append(f"Amadeus return error: {exc}")

        latency = round(time.perf_counter() - t0, 2)
        total = len(outbound_flights) + len(return_flights)
        status = "success" if total > 0 else ("failed" if errors else "success")

        return outbound_flights, return_flights, ProviderExecutionStatus(
            status=status,
            item_count=total,
            latency_seconds=latency,
            error_message=_sanitize_secrets("; ".join(errors)) if errors else None,
        )

    def _parse_amadeus_offers(
        self,
        data: Dict[str, Any],
        direction: str,
        departure_date: str,
        currency: str,
    ) -> List[AggregatedFlightOption]:
        options = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for offer in data.get("data", []):
            try:
                offer_id = str(offer.get("id") or f"amadeus_{len(options)}")
                price_val = float(offer.get("price", {}).get("total", 0.0))
                itin = offer.get("itineraries", [{}])[0]
                segs = itin.get("segments", [])
                if not segs:
                    continue

                segments = []
                for s in segs:
                    segments.append(
                        AggregatedFlightSegment(
                            carrier_code=s.get("carrierCode", ""),
                            flight_number=f"{s.get('carrierCode','')}{s.get('number','')}",
                            departure_airport=s.get("departure", {}).get("iataCode", ""),
                            arrival_airport=s.get("arrival", {}).get("iataCode", ""),
                            departure_time_local=s.get("departure", {}).get("at", ""),
                            arrival_time_local=s.get("arrival", {}).get("at", ""),
                        )
                    )

                carrier = segs[0].get("carrierCode", "Airline")
                raw_amadeus_url = offer.get("booking_url") or offer.get("deep_link") or offer.get("url")
                options.append(
                    AggregatedFlightOption(
                        flight_id=f"amadeus_{offer_id}",
                        direction=direction,
                        origin_iata=segments[0].departure_airport,
                        destination_iata=segments[-1].arrival_airport,
                        departure_date=departure_date,
                        carrier=carrier,
                        duration_minutes=120,
                        price_amount=price_val,
                        currency=currency,
                        cabin_class="economy",
                        segments=segments,
                        source_provider="Amadeus",
                        is_indicative=False,
                        price_type="live",
                        stops=max(0, len(segments) - 1),
                        retrieved_at=now_iso,
                        booking_url=str(raw_amadeus_url).strip() if raw_amadeus_url else None,
                    )
                )
            except Exception:
                continue
        return options


class SkyscannerIndicativeFlightProvider(BaseFlightProvider):
    """Secondary indicative flight provider using Skyscanner Indicative Prices API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SKYSCANNER_API_KEY", "") or getattr(settings, "SKYSCANNER_API_KEY", "")

    @property
    def name(self) -> str:
        return "Skyscanner"

    @property
    def is_indicative(self) -> bool:
        return True

    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    def search_flights(
        self,
        request: TripAggregationRequest,
        origin_airports: List[AirportCandidate],
        destination_airports: List[AirportCandidate],
    ) -> Tuple[List[AggregatedFlightOption], List[AggregatedFlightOption], ProviderExecutionStatus]:
        t0 = time.perf_counter()

        if not self.is_available():
            return [], [], ProviderExecutionStatus(
                status="unavailable",
                latency_seconds=0.0,
                error_message="SKYSCANNER_API_KEY is not configured.",
            )

        orig_iata = origin_airports[0].iata if origin_airports else "DEL"
        dest_iata = destination_airports[0].iata if destination_airports else "GOI"

        url = "https://partners.api.skyscanner.net/apiservices/v3/flights/indicative/search"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "query": {
                "market": "IN",
                "locale": "en-GB",
                "currency": request.currency,
                "queryLegs": [
                    {
                        "originPlace": {"queryPlace": {"iata": orig_iata}},
                        "destinationPlace": {"queryPlace": {"iata": dest_iata}},
                        "dateRange": {"startDate": {"year": int(request.start_date.split("-")[0]), "month": int(request.start_date.split("-")[1]), "day": int(request.start_date.split("-")[2])}},
                    }
                ],
            }
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Parse indicative quotes
                outbound = self._parse_indicative_quotes(data, "outbound", orig_iata, dest_iata, request.start_date, request.currency)
                latency = round(time.perf_counter() - t0, 2)
                return outbound, [], ProviderExecutionStatus(
                    status="success" if outbound else "partial",
                    item_count=len(outbound),
                    latency_seconds=latency,
                )
        except Exception as exc:
            latency = round(time.perf_counter() - t0, 2)
            return [], [], ProviderExecutionStatus(
                status="failed",
                latency_seconds=latency,
                error_message=_sanitize_secrets(f"Skyscanner API error: {exc}"),
            )

    def _parse_indicative_quotes(
        self,
        data: Dict[str, Any],
        direction: str,
        orig_iata: str,
        dest_iata: str,
        dep_date: str,
        currency: str,
    ) -> List[AggregatedFlightOption]:
        options = []
        quotes = data.get("content", {}).get("results", {}).get("quotes", {})
        now_iso = datetime.now(timezone.utc).isoformat()
        for q_id, q_val in quotes.items():
            price = float(q_val.get("minPrice", {}).get("amount", 0.0))
            if price <= 0:
                continue
            raw_sky_url = q_val.get("booking_url") or q_val.get("deep_link") or q_val.get("url")
            options.append(
                AggregatedFlightOption(
                    flight_id=f"skyscanner_indicative_{q_id}",
                    direction=direction,
                    origin_iata=orig_iata,
                    destination_iata=dest_iata,
                    departure_date=dep_date,
                    carrier="Indicative Airline",
                    duration_minutes=150,
                    price_amount=price,
                    currency=currency,
                    cabin_class="economy",
                    source_provider="Skyscanner",
                    is_indicative=True,
                    price_type="indicative",
                    stops=0,
                    retrieved_at=now_iso,
                    booking_url=str(raw_sky_url).strip() if raw_sky_url else None,
                )
            )
        return options


class FlightDiscoveryManager:
    """Orchestrator for provider-independent flight discovery with primary and fallback support."""

    def __init__(self, providers: Optional[List[BaseFlightProvider]] = None):
        self.providers: List[BaseFlightProvider] = providers or [
            IgnavFlightProvider(),
            AmadeusFlightProvider(),
            SkyscannerIndicativeFlightProvider(),
        ]

    def register_provider(self, provider: BaseFlightProvider) -> None:
        """Register a new flight discovery provider dynamically."""
        self.providers.append(provider)

    def discover_flights(
        self,
        request: TripAggregationRequest,
        origin_airports: List[AirportCandidate],
        destination_airports: List[AirportCandidate],
    ) -> Tuple[List[AggregatedFlightOption], List[AggregatedFlightOption], ProviderExecutionStatus]:
        """Discover flights by trying providers in priority order.

        1. Queries the primary provider (Ignav).
        2. If primary returns results, returns them directly.
        3. If primary returns 0 results, times out, or fails, attempts next available secondary provider.
        4. Preserves accurate provider attribution and is_indicative metadata.
        5. If all providers return zero results or are unconfigured, safely returns empty candidate lists.
        """
        provider_diagnostics: List[str] = []
        last_status: Optional[ProviderExecutionStatus] = None

        for idx, provider in enumerate(self.providers):
            provider_name = provider.name
            if not provider.is_available():
                logger.info(f"Flight provider '{provider_name}' is not configured/available; skipping.")
                provider_diagnostics.append(f"{provider_name}: unconfigured")
                continue

            logger.info(f"Querying flight provider [{idx + 1}/{len(self.providers)}]: '{provider_name}'...")
            try:
                outbound, return_flts, p_status = provider.search_flights(
                    request=request,
                    origin_airports=origin_airports,
                    destination_airports=destination_airports,
                )
                last_status = p_status

                total_found = len(outbound) + len(return_flts)
                if total_found > 0:
                    logger.info(
                        f"Flight discovery succeeded with '{provider_name}': {len(outbound)} outbound, "
                        f"{len(return_flts)} return candidates (indicative={provider.is_indicative})."
                    )
                    return outbound, return_flts, p_status

                provider_diagnostics.append(f"{provider_name}: 0 results ({p_status.error_message or 'no offers'})")
            except Exception as exc:
                err_msg = _sanitize_secrets(str(exc))
                logger.warning(f"Error querying flight provider '{provider_name}': {err_msg}")
                provider_diagnostics.append(f"{provider_name} error: {err_msg}")

        # If all providers yielded zero results
        summary_error = "; ".join(provider_diagnostics) if provider_diagnostics else "No active flight providers returned results."
        return [], [], ProviderExecutionStatus(
            status="unavailable" if all("unconfigured" in d for d in provider_diagnostics) else "failed",
            item_count=0,
            latency_seconds=last_status.latency_seconds if last_status else 0.0,
            error_message=_sanitize_secrets(summary_error),
        )


_flight_discovery_manager: Optional[FlightDiscoveryManager] = None


def get_flight_discovery_manager() -> FlightDiscoveryManager:
    """Singleton provider for FlightDiscoveryManager."""
    global _flight_discovery_manager
    if _flight_discovery_manager is None:
        _flight_discovery_manager = FlightDiscoveryManager()
    return _flight_discovery_manager
