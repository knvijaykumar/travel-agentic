import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_IGNAV_BASE_URL = "https://ignav.com/api"
DEFAULT_USER_AGENT = "VirtualTravelAgent/1.0 (https://github.com/travel-agentic; contact: admin@travelagentic.local)"

_ignav_service_instance: Optional["IgnavService"] = None


class IgnavError(Exception):
    """Base exception for all Ignav service errors."""
    pass


class IgnavAuthenticationError(IgnavError, ValueError):
    """Raised when authentication fails (missing API key, 401 Unauthorized, 403 Forbidden)."""
    pass


class IgnavConfigurationError(IgnavAuthenticationError):
    """Raised when IGNAV_API_KEY is not configured or missing locally."""
    pass


class IgnavNetworkError(IgnavError):
    """Raised when a network failure, connection error, or timeout occurs."""
    pass


class IgnavResponseError(IgnavError):
    """Raised when an invalid, non-JSON, or unexpected HTTP response is returned."""
    pass


class IgnavService:
    """Service to interact with the Ignav Flight Prices and Airport Search API."""

    _api_key: str = ""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize the IgnavService with an API key and base URL.

        If api_key is not provided, attempts to load from settings or environment.
        """
        if api_key is None:
            api_key = settings.IGNAV_API_KEY or os.getenv("IGNAV_API_KEY")
            if not api_key:
                env_file = Path(__file__).resolve().parents[2] / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                api_key = os.getenv("IGNAV_API_KEY")

        self._api_key: str = (api_key or "").strip()
        self.base_url: str = (base_url or getattr(settings, "IGNAV_BASE_URL", DEFAULT_IGNAV_BASE_URL)).rstrip("/")

    def __repr__(self) -> str:
        masked = f"{self._api_key[:6]}...{self._api_key[-4:]}" if len(self._api_key) > 10 else "***"
        return f"<IgnavService base_url='{self.base_url}' api_key='{masked}'>"

    def search_airports(
        self,
        query: str,
        limit: int = 10,
        timeout: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search airports by query string using Ignav API.

        Args:
            query: Airport code, city name, or search keyword (e.g. 'DEL', 'Goa', 'Mumbai').
            limit: Maximum number of airports to return (default: 10).
            timeout: Network request timeout in seconds (default: 10).

        Returns:
            List of matching airport dictionaries.

        Raises:
            IgnavAuthenticationError: If API key is missing or authentication fails (HTTP 401/403).
            IgnavNetworkError: If network error or timeout occurs.
            IgnavResponseError: If upstream API returns an invalid or unexpected response.
        """
        if not self._api_key:
            raise IgnavConfigurationError("IGNAV_API_KEY is not configured or missing.")

        if not query or not query.strip():
            return []

        params = {
            "q": query.strip(),
            "limit": str(max(1, limit)),
        }
        url = f"{self.base_url}/airports?{urllib.parse.urlencode(params)}"

        headers = {
            "X-Api-Key": self._api_key,
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            self._handle_http_error(exc, endpoint="/airports")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint="/airports")
        except json.JSONDecodeError as exc:
            raise IgnavResponseError(f"Invalid JSON response from Ignav /airports: {exc}")
        except IgnavError:
            raise
        except Exception as exc:
            raise IgnavResponseError(f"Unexpected error during Ignav /airports request: {exc}")

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if "airports" in data and isinstance(data["airports"], list):
                return data["airports"]
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            return [data]

        return []

    def search_one_way_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        cabin_class: str = "economy",
        market: str = "IN",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """Search one-way flight fares between origin and destination on a given date.

        Args:
            origin: 3-letter IATA airport or metro code for departure (e.g., 'DEL').
            destination: 3-letter IATA airport or metro code for arrival (e.g., 'GOI').
            departure_date: Departure date formatted as 'YYYY-MM-DD'.
            adults: Number of adult passengers (default: 1).
            cabin_class: Cabin class choice ('economy', 'premium_economy', 'business', 'first'; default: 'economy').
            market: 2-letter country code for pricing locale (default: 'IN').
            timeout: Network request timeout in seconds (default: 15).

        Returns:
            Dictionary containing search metadata and list of itinerary options under 'itineraries'.

        Raises:
            IgnavAuthenticationError: If API key is missing or authentication fails (HTTP 401/403).
            IgnavNetworkError: If network error or timeout occurs.
            IgnavResponseError: If upstream API returns an invalid or unexpected response.
            ValueError: If origin, destination, or departure_date are missing or empty.
        """
        if not self._api_key:
            raise IgnavConfigurationError("IGNAV_API_KEY is not configured or missing.")

        clean_origin = origin.strip().upper() if origin else ""
        clean_dest = destination.strip().upper() if destination else ""
        clean_date = departure_date.strip() if departure_date else ""

        if not clean_origin or not clean_dest or not clean_date:
            raise ValueError("origin, destination, and departure_date are required fields.")

        payload = {
            "origin": clean_origin,
            "destination": clean_dest,
            "departure_date": clean_date,
            "adults": max(1, adults),
            "cabin_class": cabin_class.strip().lower() if cabin_class else "economy",
            "market": market.strip().upper() if market else "IN",
        }

        url = f"{self.base_url}/fares/one-way"
        req_data = json.dumps(payload).encode("utf-8")

        headers = {
            "X-Api-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }

        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            self._handle_http_error(exc, endpoint="/fares/one-way")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint="/fares/one-way")
        except json.JSONDecodeError as exc:
            raise IgnavResponseError(f"Invalid JSON response from Ignav /fares/one-way: {exc}")
        except IgnavError:
            raise
        except Exception as exc:
            raise IgnavResponseError(f"Unexpected error during Ignav /fares/one-way request: {exc}")

        if isinstance(data, dict):
            if "itineraries" not in data:
                data["itineraries"] = []
            return data
        elif isinstance(data, list):
            return {
                "origin": clean_origin,
                "destination": clean_dest,
                "departure_date": clean_date,
                "itineraries": data,
            }

        return {
            "origin": clean_origin,
            "destination": clean_dest,
            "departure_date": clean_date,
            "itineraries": [],
        }

    def _handle_http_error(self, exc: urllib.error.HTTPError, endpoint: str) -> None:
        """Process HTTP error, sanitize body to protect credentials, and raise typed exception."""
        error_detail = ""
        try:
            raw_body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw_body)
                if isinstance(parsed, dict):
                    error_detail = parsed.get("message") or parsed.get("error") or raw_body
                else:
                    error_detail = raw_body
            except Exception:
                error_detail = raw_body[:300]
        except Exception:
            error_detail = exc.reason or ""

        # Redact any accidental leakage of the API key
        if self._api_key and self._api_key in error_detail:
            error_detail = error_detail.replace(self._api_key, "[REDACTED]")

        status_code = exc.code
        logger.error(f"Ignav API {endpoint} error HTTP {status_code}: {error_detail}")

        if status_code in (401, 403):
            raise IgnavAuthenticationError(
                f"Ignav API authentication failed (HTTP {status_code}): {error_detail or exc.reason}"
            )
        raise IgnavResponseError(
            f"Ignav API HTTP {status_code} error on {endpoint}: {error_detail or exc.reason}"
        )

    def _handle_network_error(self, exc: Exception, endpoint: str) -> None:
        """Process network, connection, or timeout errors and raise IgnavNetworkError."""
        msg = str(exc)
        if isinstance(exc, urllib.error.URLError):
            msg = str(exc.reason)

        logger.error(f"Ignav API network error on {endpoint}: {msg}")
        if isinstance(exc, TimeoutError) or "timed out" in msg.lower():
            raise IgnavNetworkError(f"Ignav API request to {endpoint} timed out.")
        raise IgnavNetworkError(f"Ignav API network failure on {endpoint}: {msg}")


def get_ignav_service() -> IgnavService:
    """Singleton dependency provider for IgnavService."""
    global _ignav_service_instance
    if _ignav_service_instance is None:
        _ignav_service_instance = IgnavService()
    return _ignav_service_instance

