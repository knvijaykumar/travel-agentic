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

DEFAULT_NUITEE_BASE_URL = "https://api.liteapi.travel/v3.0"
DEFAULT_NUITEE_BOOK_BASE_URL = "https://book.liteapi.travel/v3.0"
DEFAULT_USER_AGENT = "VirtualTravelAgent/1.0 (https://github.com/travel-agentic; contact: admin@travelagentic.local)"

_nuitee_service_instance: Optional["NuiteeService"] = None


class NuiteeError(Exception):
    """Base exception for all Nuitee service errors."""
    pass


class NuiteeConfigurationError(NuiteeError, ValueError):
    """Raised when NUITEE_API_KEY is not configured or missing."""
    pass


class NuiteeAuthenticationError(NuiteeError, ValueError):
    """Raised when authentication fails (missing API key, HTTP 401/403)."""
    pass


class NuiteeNetworkError(NuiteeError):
    """Raised when a network failure, connection error, or timeout occurs."""
    pass


class NuiteeResponseError(NuiteeError):
    """Raised when an invalid, non-JSON, or unexpected HTTP response is returned."""
    pass


class NuiteeService:
    """Service to interact with the Nuitee Connect (LiteAPI v3.0) Hotel API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        book_base_url: Optional[str] = None,
    ):
        """Initialize the NuiteeService with an API key, search base URL, and booking base URL.

        If api_key is not provided, attempts to load from settings or environment.
        """
        if api_key is None:
            api_key = settings.NUITEE_API_KEY or os.getenv("NUITEE_API_KEY")
            if not api_key:
                env_file = Path(__file__).resolve().parents[2] / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                api_key = os.getenv("NUITEE_API_KEY")

        self._api_key: str = (api_key or "").strip()
        self.base_url: str = (base_url or getattr(settings, "NUITEE_BASE_URL", DEFAULT_NUITEE_BASE_URL)).rstrip("/")
        self.book_base_url: str = (
            book_base_url
            or getattr(settings, "NUITEE_BOOK_BASE_URL", DEFAULT_NUITEE_BOOK_BASE_URL)
        ).rstrip("/")

    @property
    def is_sandbox(self) -> bool:
        """Indicate whether the configured API key belongs to the LiteAPI Sandbox environment."""
        return bool(self._api_key and self._api_key.startswith("sand_"))

    def __repr__(self) -> str:
        masked = f"{self._api_key[:6]}...{self._api_key[-4:]}" if len(self._api_key) > 10 else "***"
        return f"<NuiteeService base_url='{self.base_url}' api_key='{masked}'>"

    def search_hotel_rates(
        self,
        checkin: str,
        checkout: str,
        occupancies: Optional[List[Dict[str, Any]]] = None,
        adults: int = 1,
        currency: str = "INR",
        guest_nationality: str = "IN",
        city_name: Optional[str] = None,
        country_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[int] = None,
        hotel_ids: Optional[List[str]] = None,
        include_hotel_data: bool = True,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        """Search hotel rates using Nuitee Connect (LiteAPI).

        At least one location filter must be provided:
        - city_name + country_code
        - latitude + longitude (+ optional radius)
        - hotel_ids

        Args:
            checkin: Check-in date formatted as 'YYYY-MM-DD'.
            checkout: Check-out date formatted as 'YYYY-MM-DD'.
            occupancies: List of room occupancy dicts, each with 'adults' (int) and 'children' (list of ages).
            adults: Number of adults per room if occupancies is not provided (default: 1).
            currency: Currency code for pricing (default: 'INR').
            guest_nationality: 2-letter country code for guest nationality (default: 'IN').
            city_name: City name for location-based search.
            country_code: 2-letter country code (required with city_name).
            latitude: Latitude for coordinate-based search.
            longitude: Longitude for coordinate-based search.
            radius: Search radius in km for coordinate-based search.
            hotel_ids: List of specific hotel IDs to query.
            include_hotel_data: Whether to include hotel metadata in response (default: True).
            timeout: Network request timeout in seconds (default: 20).

        Returns:
            Dictionary containing hotel rate data from LiteAPI.

        Raises:
            NuiteeConfigurationError: If API key is not configured.
            NuiteeAuthenticationError: If authentication fails (HTTP 401/403).
            NuiteeNetworkError: If network error or timeout occurs.
            NuiteeResponseError: If upstream API returns an invalid or unexpected response.
            ValueError: If no location filter is provided or required dates are missing.
        """
        if not self._api_key:
            raise NuiteeConfigurationError("NUITEE_API_KEY is not configured or missing.")

        clean_checkin = checkin.strip() if checkin else ""
        clean_checkout = checkout.strip() if checkout else ""
        if not clean_checkin or not clean_checkout:
            raise ValueError("checkin and checkout dates are required.")

        # Validate location filters
        has_city = bool(city_name and city_name.strip())
        has_coords = latitude is not None and longitude is not None
        has_hotel_ids = bool(hotel_ids)

        if not has_city and not has_coords and not has_hotel_ids:
            raise ValueError(
                "At least one location filter is required: "
                "city_name + country_code, latitude + longitude, or hotel_ids."
            )

        # Build occupancies
        if occupancies is None:
            occupancies = [{"adults": max(1, adults), "children": []}]

        payload: Dict[str, Any] = {
            "checkin": clean_checkin,
            "checkout": clean_checkout,
            "occupancies": occupancies,
            "currency": currency.strip().upper() if currency else "INR",
            "guestNationality": guest_nationality.strip().upper() if guest_nationality else "IN",
        }

        if has_city:
            payload["cityName"] = city_name.strip()
            if country_code:
                payload["countryCode"] = country_code.strip().upper()

        if has_coords:
            payload["latitude"] = latitude
            payload["longitude"] = longitude
            if radius is not None:
                payload["radius"] = radius

        if has_hotel_ids:
            payload["hotelIds"] = hotel_ids

        if include_hotel_data:
            payload["includeHotelData"] = True

        url = f"{self.base_url}/hotels/rates"
        req_data = json.dumps(payload).encode("utf-8")

        headers = {
            "X-API-Key": self._api_key,
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
            self._handle_http_error(exc, endpoint="/hotels/rates")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint="/hotels/rates")
        except json.JSONDecodeError as exc:
            raise NuiteeResponseError(f"Invalid JSON response from Nuitee /hotels/rates: {exc}")
        except NuiteeError:
            raise
        except Exception as exc:
            raise NuiteeResponseError(f"Unexpected error during Nuitee /hotels/rates request: {exc}")

        if isinstance(data, dict):
            return data

        return {"data": [], "hotels": []}

    def get_hotel_details(
        self,
        hotel_id: str,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """Retrieve detailed information about a specific hotel.

        Args:
            hotel_id: The unique hotel identifier from LiteAPI.
            timeout: Network request timeout in seconds (default: 15).

        Returns:
            Dictionary containing hotel detail data from LiteAPI.

        Raises:
            NuiteeConfigurationError: If API key is not configured.
            NuiteeAuthenticationError: If authentication fails (HTTP 401/403).
            NuiteeNetworkError: If network error or timeout occurs.
            NuiteeResponseError: If upstream API returns an invalid or unexpected response.
            ValueError: If hotel_id is missing or empty.
        """
        if not self._api_key:
            raise NuiteeConfigurationError("NUITEE_API_KEY is not configured or missing.")

        clean_id = hotel_id.strip() if hotel_id else ""
        if not clean_id:
            raise ValueError("hotel_id is required.")

        params = urllib.parse.urlencode({"hotelId": clean_id})
        url = f"{self.base_url}/data/hotel?{params}"

        headers = {
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            self._handle_http_error(exc, endpoint="/data/hotel")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint="/data/hotel")
        except json.JSONDecodeError as exc:
            raise NuiteeResponseError(f"Invalid JSON response from Nuitee /data/hotel: {exc}")
        except NuiteeError:
            raise
        except Exception as exc:
            raise NuiteeResponseError(f"Unexpected error during Nuitee /data/hotel request: {exc}")

        if isinstance(data, dict):
            return data

        return {}

    def prebook_rate(
        self,
        offer_id: str,
        use_payment_sdk: bool = False,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        """Pre-book a hotel rate offer to lock in the rate and obtain a prebookId.

        Endpoint: POST https://book.liteapi.travel/v3.0/rates/prebook

        Args:
            offer_id: The unique rate offer ID returned from search_hotel_rates.
            use_payment_sdk: Whether payment is handled via LiteAPI JS SDK (False for direct server-to-server).
            timeout: Network request timeout in seconds (default: 20).

        Returns:
            Dictionary containing pre-booking data including 'prebookId', pricing, and cancellation policy.

        Raises:
            NuiteeConfigurationError: If API key is not configured.
            NuiteeAuthenticationError: If authentication fails (HTTP 401/403).
            NuiteeNetworkError: If network error or timeout occurs.
            NuiteeResponseError: If upstream API returns an error or invalid response.
            ValueError: If offer_id is missing or empty.
        """
        if not self._api_key:
            raise NuiteeConfigurationError("NUITEE_API_KEY is not configured or missing.")

        clean_offer_id = offer_id.strip() if offer_id else ""
        if not clean_offer_id:
            raise ValueError("offer_id is required.")

        payload = {
            "offerId": clean_offer_id,
            "usePaymentSdk": use_payment_sdk,
        }
        url = f"{self.book_base_url}/rates/prebook"
        req_data = json.dumps(payload).encode("utf-8")

        headers = {
            "X-API-Key": self._api_key,
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
            self._handle_http_error(exc, endpoint="/rates/prebook")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint="/rates/prebook")
        except json.JSONDecodeError as exc:
            raise NuiteeResponseError(f"Invalid JSON response from Nuitee /rates/prebook: {exc}")
        except NuiteeError:
            raise
        except Exception as exc:
            raise NuiteeResponseError(f"Unexpected error during Nuitee /rates/prebook request: {exc}")

        if isinstance(data, dict):
            return data

        return {}

    def book_hotel(
        self,
        prebook_id: str,
        holder: Dict[str, Any],
        client_reference: Optional[str] = None,
        payment_method: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Confirm a hotel booking using a valid prebookId and guest details.

        Endpoint: POST https://book.liteapi.travel/v3.0/rates/book

        Args:
            prebook_id: The prebookId obtained from prebook_rate.
            holder: Guest holder details containing firstName, lastName, email, and optional phone.
            client_reference: Optional booking reference / correlation ID.
            payment_method: Payment method (defaults to 'ACC_CREDIT_CARD' for sandbox).
            timeout: Network request timeout in seconds (default: 30).

        Returns:
            Dictionary containing booking confirmation details, status, and bookingId.

        Raises:
            NuiteeConfigurationError: If API key is not configured.
            NuiteeAuthenticationError: If authentication fails (HTTP 401/403).
            NuiteeNetworkError: If network error or timeout occurs.
            NuiteeResponseError: If upstream API returns an error or invalid response.
            ValueError: If prebook_id or required guest details are missing.
        """
        if not self._api_key:
            raise NuiteeConfigurationError("NUITEE_API_KEY is not configured or missing.")

        clean_prebook_id = prebook_id.strip() if prebook_id else ""
        if not clean_prebook_id:
            raise ValueError("prebook_id is required.")

        first_name = (holder.get("firstName") or holder.get("first_name") or "").strip()
        last_name = (holder.get("lastName") or holder.get("last_name") or "").strip()
        email = (holder.get("email") or "").strip()
        phone = (holder.get("phone") or "").strip()

        if not first_name or not last_name:
            raise ValueError("Guest first and last name are required.")
        if not email:
            raise ValueError("Guest email is required.")

        method = payment_method or ("ACC_CREDIT_CARD" if self.is_sandbox else "ACC_CREDIT_CARD")

        payload: Dict[str, Any] = {
            "prebookId": clean_prebook_id,
            "holder": {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
            },
            "payment": {
                "method": method,
            },
        }
        if phone:
            payload["holder"]["phone"] = phone
        if client_reference:
            payload["clientReference"] = client_reference.strip()

        url = f"{self.book_base_url}/rates/book"
        req_data = json.dumps(payload).encode("utf-8")

        headers = {
            "X-API-Key": self._api_key,
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
            self._handle_http_error(exc, endpoint="/rates/book")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint="/rates/book")
        except json.JSONDecodeError as exc:
            raise NuiteeResponseError(f"Invalid JSON response from Nuitee /rates/book: {exc}")
        except NuiteeError:
            raise
        except Exception as exc:
            raise NuiteeResponseError(f"Unexpected error during Nuitee /rates/book request: {exc}")

        if isinstance(data, dict):
            return data

        return {}

    def get_booking_details(
        self,
        booking_id: str,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """Retrieve booking details and current confirmation status for a booking.

        Endpoint: GET https://book.liteapi.travel/v3.0/bookings/{bookingId}

        Args:
            booking_id: The LiteAPI booking identifier.
            timeout: Network request timeout in seconds (default: 15).

        Returns:
            Dictionary containing booking status and hotel stay details.

        Raises:
            NuiteeConfigurationError: If API key is not configured.
            NuiteeAuthenticationError: If authentication fails (HTTP 401/403).
            NuiteeNetworkError: If network error or timeout occurs.
            NuiteeResponseError: If upstream API returns an error or invalid response.
            ValueError: If booking_id is missing or empty.
        """
        if not self._api_key:
            raise NuiteeConfigurationError("NUITEE_API_KEY is not configured or missing.")

        clean_id = booking_id.strip() if booking_id else ""
        if not clean_id:
            raise ValueError("booking_id is required.")

        url = f"{self.book_base_url}/bookings/{urllib.parse.quote(clean_id)}"

        headers = {
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            self._handle_http_error(exc, endpoint=f"/bookings/{clean_id}")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint=f"/bookings/{clean_id}")
        except json.JSONDecodeError as exc:
            raise NuiteeResponseError(f"Invalid JSON response from Nuitee /bookings/{clean_id}: {exc}")
        except NuiteeError:
            raise
        except Exception as exc:
            raise NuiteeResponseError(f"Unexpected error during Nuitee /bookings/{clean_id} request: {exc}")

        if isinstance(data, dict):
            return data

        return {}

    def cancel_booking(
        self,
        booking_id: str,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """Cancel a confirmed hotel booking.

        Endpoint: PUT https://book.liteapi.travel/v3.0/bookings/{bookingId}

        Args:
            booking_id: The LiteAPI booking identifier to cancel.
            timeout: Network request timeout in seconds (default: 15).

        Returns:
            Dictionary containing cancellation status, fee, and refund details.

        Raises:
            NuiteeConfigurationError: If API key is not configured.
            NuiteeAuthenticationError: If authentication fails (HTTP 401/403).
            NuiteeNetworkError: If network error or timeout occurs.
            NuiteeResponseError: If upstream API returns an error or invalid response.
            ValueError: If booking_id is missing or empty.
        """
        if not self._api_key:
            raise NuiteeConfigurationError("NUITEE_API_KEY is not configured or missing.")

        clean_id = booking_id.strip() if booking_id else ""
        if not clean_id:
            raise ValueError("booking_id is required.")

        url = f"{self.book_base_url}/bookings/{urllib.parse.quote(clean_id)}"

        headers = {
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }

        req = urllib.request.Request(url, headers=headers, method="PUT")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            self._handle_http_error(exc, endpoint=f"/bookings/{clean_id} (cancel)")
        except (urllib.error.URLError, TimeoutError) as exc:
            self._handle_network_error(exc, endpoint=f"/bookings/{clean_id} (cancel)")
        except json.JSONDecodeError as exc:
            raise NuiteeResponseError(f"Invalid JSON response from Nuitee cancel /bookings/{clean_id}: {exc}")
        except NuiteeError:
            raise
        except Exception as exc:
            raise NuiteeResponseError(f"Unexpected error during Nuitee cancel /bookings/{clean_id} request: {exc}")

        if isinstance(data, dict):
            return data

        return {}

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
        detail = error_detail or str(exc.reason or "")
        if self._api_key and self._api_key in detail:
            detail = detail.replace(self._api_key, "[REDACTED]")

        logger.error(f"Nuitee API {endpoint} error HTTP {status_code}: {detail}")

        if status_code in (401, 403):
            raise NuiteeAuthenticationError(
                f"Nuitee API authentication failed (HTTP {status_code}): {detail}"
            )
        raise NuiteeResponseError(
            f"Nuitee API HTTP {status_code} error on {endpoint}: {detail}"
        )

    def _handle_network_error(self, exc: Exception, endpoint: str) -> None:
        """Process network, connection, or timeout errors and raise NuiteeNetworkError."""
        msg = str(exc)
        if isinstance(exc, urllib.error.URLError):
            msg = str(exc.reason)

        logger.error(f"Nuitee API network error on {endpoint}: {msg}")
        if isinstance(exc, TimeoutError) or "timed out" in msg.lower():
            raise NuiteeNetworkError(f"Nuitee API request to {endpoint} timed out.")
        raise NuiteeNetworkError(f"Nuitee API network failure on {endpoint}: {msg}")


def get_nuitee_service() -> NuiteeService:
    """Singleton dependency provider for NuiteeService."""
    global _nuitee_service_instance
    if _nuitee_service_instance is None:
        _nuitee_service_instance = NuiteeService()
    return _nuitee_service_instance

