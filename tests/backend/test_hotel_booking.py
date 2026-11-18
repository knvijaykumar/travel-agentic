import io
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError

from backend.app.api.v1.endpoints.bookings import (
    router as bookings_router,
    prebook_hotel_rate,
    confirm_hotel_booking,
    get_hotel_booking,
    cancel_hotel_booking,
)
from backend.app.api.v1.router import api_router
from backend.app.schemas.booking import (
    HotelGuestHolder,
    HotelPrebookRequest,
    HotelPrebookResponse,
    HotelBookingConfirmationRequest,
    HotelBookingConfirmationResponse,
    HotelBookingCancellationResponse,
)
from backend.app.services.nuitee_service import (
    NuiteeService,
    NuiteeConfigurationError,
    NuiteeAuthenticationError,
    NuiteeNetworkError,
    NuiteeResponseError,
)


# ==============================================================================
# SAMPLE FIXTURES AND PAYLOADS
# ==============================================================================

SAMPLE_PREBOOK_LITEAPI_RESPONSE = {
    "data": {
        "prebookId": "pb_live_abc12345678",
        "price": {
            "amount": 9500.0,
            "currency": "INR",
        },
        "cancellationPolicies": {
            "refundable": True,
            "description": "Free cancellation until 48 hours before check-in.",
        },
        "room": {
            "name": "Deluxe Ocean View Room",
        },
    }
}

SAMPLE_BOOK_LITEAPI_RESPONSE = {
    "data": {
        "bookingId": "bk_confirmed_998877",
        "status": "CONFIRMED",
        "hotelConfirmationCode": "HTL-WANDER-789",
        "checkin": "2026-12-15",
        "checkout": "2026-12-17",
        "hotel": {
            "hotelId": "lp_goa_hyatt",
            "name": "Grand Hyatt Goa",
        },
        "holder": {
            "firstName": "Rahul",
            "lastName": "Sharma",
            "email": "rahul.sharma@example.com",
            "phone": "+919876543210",
        },
        "price": {
            "amount": 9500.0,
            "currency": "INR",
        },
        "cancellationPolicies": {
            "refundable": True,
            "description": "Free cancellation until 48 hours before check-in.",
        },
        "createdAt": "2026-11-10T11:00:00Z",
    }
}

SAMPLE_CANCEL_LITEAPI_RESPONSE = {
    "data": {
        "bookingId": "bk_confirmed_998877",
        "status": "CANCELLED",
        "cancellationFee": 0.0,
        "refundAmount": 9500.0,
        "currency": "INR",
        "message": "Booking was cancelled without fee.",
    }
}


def _create_mock_response(status_code: int = 200, json_data: dict = None) -> MagicMock:
    """Helper to mock urllib.request.urlopen response."""
    content = json.dumps(json_data or {}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = content
    mock_resp.status = status_code
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    return mock_resp


# ==============================================================================
# 1. SCHEMA VALIDATION TESTS
# ==============================================================================

class TestBookingSchemas:
    """Verify strict validation and safety rules for booking Pydantic schemas."""

    def test_hotel_guest_holder_valid(self):
        holder = HotelGuestHolder(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="+919876543210",
        )
        assert holder.first_name == "Jane"
        assert holder.last_name == "Doe"
        assert holder.email == "jane.doe@example.com"
        assert holder.phone == "+919876543210"

    def test_hotel_guest_holder_invalid_email(self):
        with pytest.raises(ValidationError) as exc:
            HotelGuestHolder(
                first_name="Jane",
                last_name="Doe",
                email="not-an-email",
            )
        assert "valid email address is required" in str(exc.value)

    def test_hotel_guest_holder_empty_name(self):
        with pytest.raises(ValidationError) as exc:
            HotelGuestHolder(
                first_name="  ",
                last_name="Doe",
                email="jane@example.com",
            )
        assert "Name cannot be empty" in str(exc.value)

    def test_hotel_prebook_request_valid(self):
        req = HotelPrebookRequest(offer_id="offer_xyz_987", use_payment_sdk=False)
        assert req.offer_id == "offer_xyz_987"
        assert req.use_payment_sdk is False

    def test_hotel_prebook_request_empty_offer_id(self):
        with pytest.raises(ValidationError):
            HotelPrebookRequest(offer_id="   ")

    def test_hotel_booking_confirmation_request_valid(self):
        req = HotelBookingConfirmationRequest(
            prebook_id="pb_abc_123",
            holder=HotelGuestHolder(
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
            ),
            client_reference="REF-001",
        )
        assert req.prebook_id == "pb_abc_123"
        assert req.holder.first_name == "Jane"
        assert req.payment_method == "ACC_CREDIT_CARD"

    def test_hotel_booking_confirmation_request_empty_prebook_id(self):
        with pytest.raises(ValidationError):
            HotelBookingConfirmationRequest(
                prebook_id="",
                holder=HotelGuestHolder(
                    first_name="Jane",
                    last_name="Doe",
                    email="jane@example.com",
                ),
            )


# ==============================================================================
# 2. NUITEE SERVICE UNIT TESTS (MOCKED HTTP)
# ==============================================================================

class TestNuiteeServiceBookingMethods:
    """Verify NuiteeService booking methods with mocked network calls."""

    @patch("urllib.request.urlopen")
    def test_prebook_rate_success(self, mock_urlopen):
        mock_urlopen.return_value = _create_mock_response(200, SAMPLE_PREBOOK_LITEAPI_RESPONSE)
        service = NuiteeService(api_key="sand_test_key_123")

        result = service.prebook_rate(offer_id="offer_123", use_payment_sdk=False)
        assert "data" in result
        assert result["data"]["prebookId"] == "pb_live_abc12345678"

        # Verify request parameters
        req_arg = mock_urlopen.call_args[0][0]
        assert req_arg.get_method() == "POST"
        assert "/rates/prebook" in req_arg.full_url
        assert req_arg.get_header("X-api-key") == "sand_test_key_123"
        payload = json.loads(req_arg.data.decode("utf-8"))
        assert payload["offerId"] == "offer_123"
        assert payload["usePaymentSdk"] is False

    def test_prebook_rate_unconfigured(self):
        service = NuiteeService(api_key="")
        with pytest.raises(NuiteeConfigurationError):
            service.prebook_rate(offer_id="offer_123")

    def test_prebook_rate_missing_offer_id(self):
        service = NuiteeService(api_key="sand_key")
        with pytest.raises(ValueError):
            service.prebook_rate(offer_id="  ")

    @patch("urllib.request.urlopen")
    def test_prebook_rate_expired_or_unavailable(self, mock_urlopen):
        error_body = json.dumps({"error": "Offer expired or not found"}).encode("utf-8")
        fp = io.BytesIO(error_body)
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://book.liteapi.travel/v3.0/rates/prebook",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=fp,
        )
        service = NuiteeService(api_key="sand_key")
        with pytest.raises(NuiteeResponseError) as exc:
            service.prebook_rate(offer_id="expired_offer")
        assert "HTTP 400" in str(exc.value)

    @patch("urllib.request.urlopen")
    def test_book_hotel_success(self, mock_urlopen):
        mock_urlopen.return_value = _create_mock_response(200, SAMPLE_BOOK_LITEAPI_RESPONSE)
        service = NuiteeService(api_key="sand_key_abc")

        holder = {
            "first_name": "Rahul",
            "last_name": "Sharma",
            "email": "rahul@example.com",
            "phone": "+919876543210",
        }
        res = service.book_hotel(
            prebook_id="pb_live_abc12345678",
            holder=holder,
            client_reference="WANDER-101",
        )
        assert res["data"]["bookingId"] == "bk_confirmed_998877"
        assert res["data"]["status"] == "CONFIRMED"

        # Verify request parameters
        req_arg = mock_urlopen.call_args[0][0]
        assert req_arg.get_method() == "POST"
        assert "/rates/book" in req_arg.full_url
        payload = json.loads(req_arg.data.decode("utf-8"))
        assert payload["prebookId"] == "pb_live_abc12345678"
        assert payload["holder"]["firstName"] == "Rahul"
        assert payload["holder"]["lastName"] == "Sharma"
        assert payload["payment"]["method"] == "ACC_CREDIT_CARD"
        assert payload["clientReference"] == "WANDER-101"

    def test_book_hotel_missing_guest_name(self):
        service = NuiteeService(api_key="sand_key")
        with pytest.raises(ValueError) as exc:
            service.book_hotel(
                prebook_id="pb_123",
                holder={"first_name": "", "last_name": "Sharma", "email": "r@ex.com"},
            )
        assert "Guest first and last name are required" in str(exc.value)

    @patch("urllib.request.urlopen")
    def test_get_booking_details_success(self, mock_urlopen):
        mock_urlopen.return_value = _create_mock_response(200, SAMPLE_BOOK_LITEAPI_RESPONSE)
        service = NuiteeService(api_key="sand_key")

        res = service.get_booking_details(booking_id="bk_confirmed_998877")
        assert res["data"]["bookingId"] == "bk_confirmed_998877"

        req_arg = mock_urlopen.call_args[0][0]
        assert req_arg.get_method() == "GET"
        assert "/bookings/bk_confirmed_998877" in req_arg.full_url

    @patch("urllib.request.urlopen")
    def test_cancel_booking_success(self, mock_urlopen):
        mock_urlopen.return_value = _create_mock_response(200, SAMPLE_CANCEL_LITEAPI_RESPONSE)
        service = NuiteeService(api_key="sand_key")

        res = service.cancel_booking(booking_id="bk_confirmed_998877")
        assert res["data"]["status"] == "CANCELLED"
        assert res["data"]["refundAmount"] == 9500.0

        req_arg = mock_urlopen.call_args[0][0]
        # Must be HTTP PUT method per LiteAPI v3 documentation
        assert req_arg.get_method() == "PUT"
        assert "/bookings/bk_confirmed_998877" in req_arg.full_url

    def test_sandbox_flag_detection(self):
        sandbox_service = NuiteeService(api_key="sand_test_999")
        assert sandbox_service.is_sandbox is True

        prod_service = NuiteeService(api_key="live_production_key_123")
        assert prod_service.is_sandbox is False

    @patch("urllib.request.urlopen")
    def test_credential_sanitization_on_error(self, mock_urlopen):
        secret = "sand_ultra_secret_key_9999"
        error_body = f'{{"error": "Forbidden key {secret}"}}'.encode("utf-8")
        fp = io.BytesIO(error_body)
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://book.liteapi.travel/v3.0/rates/prebook",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=fp,
        )
        service = NuiteeService(api_key=secret)
        with pytest.raises(NuiteeAuthenticationError) as exc:
            service.prebook_rate(offer_id="offer_123")

        # Crucial check: raw secret key MUST NOT appear in the raised exception string
        assert secret not in str(exc.value)
        assert "[REDACTED]" in str(exc.value)


# ==============================================================================
# 3. FASTAPI BOOKING ROUTE ENDPOINT BEHAVIORAL TESTS
# ==============================================================================

class TestBookingEndpointsBehavior:
    """Test FastAPI booking endpoints directly with mocked NuiteeService."""

    def test_prebook_endpoint_success(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.is_sandbox = True
        mock_service.prebook_rate.return_value = SAMPLE_PREBOOK_LITEAPI_RESPONSE

        req = HotelPrebookRequest(offer_id="offer_abc123", use_payment_sdk=False)
        result = prebook_hotel_rate(request=req, nuitee_service=mock_service)

        assert isinstance(result, HotelPrebookResponse)
        assert result.prebook_id == "pb_live_abc12345678"
        assert result.offer_id == "offer_abc123"
        assert result.price_amount == 9500.0
        assert result.currency == "INR"
        assert result.is_sandbox is True
        assert "Free cancellation" in result.cancellation_policy

    def test_prebook_endpoint_provider_unavailable_or_expired(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.prebook_rate.side_effect = NuiteeResponseError("Nuitee API HTTP 400 error: Rate offer expired")

        req = HotelPrebookRequest(offer_id="offer_expired")
        with pytest.raises(HTTPException) as exc:
            prebook_hotel_rate(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Rate offer is unavailable or expired" in exc.value.detail

    def test_prebook_endpoint_provider_unconfigured(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.prebook_rate.side_effect = NuiteeConfigurationError("Missing API key")

        req = HotelPrebookRequest(offer_id="offer_123")
        with pytest.raises(HTTPException) as exc:
            prebook_hotel_rate(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_prebook_endpoint_provider_timeout(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.prebook_rate.side_effect = NuiteeNetworkError("Request timed out")

        req = HotelPrebookRequest(offer_id="offer_123")
        with pytest.raises(HTTPException) as exc:
            prebook_hotel_rate(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    def test_prebook_endpoint_provider_auth_failure(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.prebook_rate.side_effect = NuiteeAuthenticationError("Nuitee API authentication failed (HTTP 401)")

        req = HotelPrebookRequest(offer_id="offer_123")
        with pytest.raises(HTTPException) as exc:
            prebook_hotel_rate(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_502_BAD_GATEWAY

    def test_confirm_hotel_booking_endpoint_success(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.is_sandbox = True
        mock_service.book_hotel.return_value = SAMPLE_BOOK_LITEAPI_RESPONSE

        req = HotelBookingConfirmationRequest(
            prebook_id="pb_live_abc12345678",
            holder=HotelGuestHolder(
                first_name="Rahul",
                last_name="Sharma",
                email="rahul.sharma@example.com",
                phone="+919876543210",
            ),
            client_reference="VTA-GOA-2026",
            payment_method="ACC_CREDIT_CARD",
        )

        result = confirm_hotel_booking(request=req, nuitee_service=mock_service)
        assert isinstance(result, HotelBookingConfirmationResponse)
        assert result.booking_id == "bk_confirmed_998877"
        assert result.status == "CONFIRMED"
        assert result.hotel_confirmation_code == "HTL-WANDER-789"
        assert result.hotel_name == "Grand Hyatt Goa"
        assert result.guest_name == "Rahul Sharma"
        assert result.total_price == 9500.0
        assert result.is_sandbox is True

    def test_confirm_hotel_booking_provider_expired_session(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.book_hotel.side_effect = NuiteeResponseError("Nuitee API HTTP 400 error: Prebook session expired")

        req = HotelBookingConfirmationRequest(
            prebook_id="pb_expired_session",
            holder=HotelGuestHolder(
                first_name="Rahul",
                last_name="Sharma",
                email="rahul@example.com",
            ),
        )
        with pytest.raises(HTTPException) as exc:
            confirm_hotel_booking(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Hotel booking failed with provider" in exc.value.detail

    def test_confirm_hotel_booking_provider_unconfigured(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.book_hotel.side_effect = NuiteeConfigurationError("Missing API key")

        req = HotelBookingConfirmationRequest(
            prebook_id="pb_123",
            holder=HotelGuestHolder(
                first_name="Rahul",
                last_name="Sharma",
                email="rahul@example.com",
            ),
        )
        with pytest.raises(HTTPException) as exc:
            confirm_hotel_booking(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_confirm_hotel_booking_provider_timeout(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.book_hotel.side_effect = NuiteeNetworkError("Request timed out")

        req = HotelBookingConfirmationRequest(
            prebook_id="pb_123",
            holder=HotelGuestHolder(
                first_name="Rahul",
                last_name="Sharma",
                email="rahul@example.com",
            ),
        )
        with pytest.raises(HTTPException) as exc:
            confirm_hotel_booking(request=req, nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    def test_get_hotel_booking_endpoint_success(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.is_sandbox = True
        mock_service.get_booking_details.return_value = SAMPLE_BOOK_LITEAPI_RESPONSE

        result = get_hotel_booking(booking_id="bk_confirmed_998877", nuitee_service=mock_service)
        assert isinstance(result, HotelBookingConfirmationResponse)
        assert result.booking_id == "bk_confirmed_998877"
        assert result.hotel_name == "Grand Hyatt Goa"

    def test_get_hotel_booking_endpoint_not_found(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.get_booking_details.side_effect = NuiteeResponseError("Nuitee API HTTP 404 error: Booking not found")

        with pytest.raises(HTTPException) as exc:
            get_hotel_booking(booking_id="bk_non_existent", nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_hotel_booking_endpoint_success(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.is_sandbox = True
        mock_service.cancel_booking.return_value = SAMPLE_CANCEL_LITEAPI_RESPONSE

        result = cancel_hotel_booking(booking_id="bk_confirmed_998877", nuitee_service=mock_service)
        assert isinstance(result, HotelBookingCancellationResponse)
        assert result.booking_id == "bk_confirmed_998877"
        assert result.status == "CANCELLED"
        assert result.refund_amount == 9500.0
        assert result.cancellation_fee == 0.0

    def test_cancel_hotel_booking_endpoint_rejected_by_policy(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.cancel_booking.side_effect = NuiteeResponseError(
            "Nuitee API HTTP 400 error: Booking non-refundable after check-in deadline"
        )

        with pytest.raises(HTTPException) as exc:
            cancel_hotel_booking(booking_id="bk_confirmed_998877", nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cancellation rejected by hotel provider" in exc.value.detail

    def test_cancel_hotel_booking_endpoint_not_found(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.cancel_booking.side_effect = NuiteeResponseError("Nuitee API HTTP 404 error: Booking not found")

        with pytest.raises(HTTPException) as exc:
            cancel_hotel_booking(booking_id="bk_non_existent", nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_hotel_booking_endpoint_timeout(self):
        mock_service = MagicMock(spec=NuiteeService)
        mock_service.cancel_booking.side_effect = NuiteeNetworkError("Request timed out")

        with pytest.raises(HTTPException) as exc:
            cancel_hotel_booking(booking_id="bk_123", nuitee_service=mock_service)
        assert exc.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT


# ==============================================================================
# 4. ROUTER REGISTRATION TESTS
# ==============================================================================

class TestRouterRegistration:
    """Verify booking router endpoints are registered correctly in FastAPI routing table."""

    def test_bookings_router_routes(self):
        route_paths = [r.path for r in bookings_router.routes]
        assert "/bookings/hotels/prebook" in route_paths
        assert "/bookings/hotels/book" in route_paths
        assert "/bookings/hotels/{booking_id}" in route_paths
        assert "/bookings/hotels/{booking_id}/cancel" in route_paths

    def test_api_router_includes_bookings(self):
        included_routers = [
            getattr(r, "original_router", getattr(r, "included_router", None))
            for r in api_router.routes
        ]
        assert bookings_router in included_routers
