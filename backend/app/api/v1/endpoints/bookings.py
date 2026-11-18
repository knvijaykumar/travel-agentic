import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.booking import (
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
    get_nuitee_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "/hotels/prebook",
    summary="Pre-book hotel rate offer",
    response_model=HotelPrebookResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Offer pre-booked successfully; rate is locked and prebookId returned."},
        400: {"description": "Offer expired, unavailable, or rate changed."},
        422: {"description": "Validation error in request parameters."},
        502: {"description": "Upstream LiteAPI error or authentication failure."},
        503: {"description": "Hotel booking provider not configured."},
        504: {"description": "Provider connection timed out."},
    },
)
def prebook_hotel_rate(
    request: HotelPrebookRequest,
    nuitee_service: NuiteeService = Depends(get_nuitee_service),
) -> HotelPrebookResponse:
    """Pre-book a hotel room rate to verify rate availability and obtain a prebookId.

    NOTE: This step locks the rate and cancellation terms temporarily.
    It does NOT confirm the booking or incur any financial charges.
    """
    logger.info("Initiating hotel rate prebook for offer_id: %s", request.offer_id)

    try:
        raw_res = nuitee_service.prebook_rate(
            offer_id=request.offer_id,
            use_payment_sdk=request.use_payment_sdk,
        )

        data = raw_res.get("data") or {}
        if not data and isinstance(raw_res, dict):
            # In case response is not nested under data
            data = raw_res

        prebook_id = data.get("prebookId") or data.get("prebook_id")
        if not prebook_id:
            logger.warning("LiteAPI prebook succeeded but returned no prebookId: %s", data)
            raise NuiteeResponseError("Hotel booking provider did not return a valid prebookId.")

        # Extract price
        price_obj = data.get("price") or {}
        if isinstance(price_obj, dict):
            price_amount = float(price_obj.get("amount") or price_obj.get("total") or 0.0)
            currency = str(price_obj.get("currency") or "INR")
        elif isinstance(price_obj, (int, float)):
            price_amount = float(price_obj)
            currency = "INR"
        else:
            price_amount = 0.0
            currency = "INR"

        # Extract cancellation policy
        canc_pol = data.get("cancellationPolicies")
        canc_policy_str = None
        if isinstance(canc_pol, dict):
            canc_policy_str = canc_pol.get("description") or canc_pol.get("policyText")
            if not canc_policy_str and canc_pol.get("refundable") is True:
                canc_policy_str = "Free cancellation available"
            elif not canc_policy_str and canc_pol.get("refundable") is False:
                canc_policy_str = "Non-refundable"
        elif isinstance(canc_pol, str):
            canc_policy_str = canc_pol

        room_obj = data.get("room") or {}
        room_name = room_obj.get("name") if isinstance(room_obj, dict) else None

        return HotelPrebookResponse(
            prebook_id=prebook_id,
            offer_id=request.offer_id,
            price_amount=price_amount,
            currency=currency,
            cancellation_policy=canc_policy_str,
            room_name=room_name,
            is_sandbox=nuitee_service.is_sandbox,
            raw_data=data,
        )

    except NuiteeConfigurationError as exc:
        logger.error("Hotel provider configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel booking provider is not configured.",
        )
    except NuiteeAuthenticationError as exc:
        logger.error("Hotel provider authentication error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hotel provider authentication failed.",
        )
    except NuiteeNetworkError as exc:
        logger.error("Hotel provider network error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Hotel booking provider connection timed out.",
        )
    except NuiteeResponseError as exc:
        logger.warning("Hotel provider prebook response error: %s", exc)
        msg = str(exc)
        if any(code in msg for code in ("HTTP 400", "HTTP 404", "HTTP 422")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rate offer is unavailable or expired: {msg}",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hotel booking provider error: {msg}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.post(
    "/hotels/book",
    summary="Confirm hotel booking",
    response_model=HotelBookingConfirmationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Hotel booking confirmed successfully."},
        400: {"description": "Prebook expired or booking rejected by provider."},
        422: {"description": "Validation error in guest or prebook parameters."},
        502: {"description": "Upstream provider booking execution failure."},
        503: {"description": "Hotel booking provider not configured."},
        504: {"description": "Provider connection timed out."},
    },
)
def confirm_hotel_booking(
    request: HotelBookingConfirmationRequest,
    nuitee_service: NuiteeService = Depends(get_nuitee_service),
) -> HotelBookingConfirmationResponse:
    """Explicitly confirm a hotel booking with guest contact and payment authorization.

    CRITICAL ARCHITECTURAL SAFEGUARD:
    This endpoint MUST only be invoked upon explicit confirmation by the user.
    Never trigger this endpoint implicitly, automatically, or during itinerary generation.
    """
    logger.info(
        "Confirming hotel booking for prebook_id: %s (guest: %s %s, sandbox=%s)",
        request.prebook_id,
        request.holder.first_name,
        request.holder.last_name,
        nuitee_service.is_sandbox,
    )

    try:
        raw_res = nuitee_service.book_hotel(
            prebook_id=request.prebook_id,
            holder=request.holder.model_dump(),
            client_reference=request.client_reference,
            payment_method=request.payment_method,
        )

        data = raw_res.get("data") or {}
        if not data and isinstance(raw_res, dict):
            data = raw_res

        booking_id = data.get("bookingId") or data.get("booking_id")
        if not booking_id:
            logger.error("LiteAPI book response missing bookingId: %s", data)
            raise NuiteeResponseError("Hotel booking provider did not return a valid bookingId.")

        booking_status = data.get("status") or "CONFIRMED"
        confirmation_code = data.get("hotelConfirmationCode") or data.get("confirmationCode")
        checkin = data.get("checkin")
        checkout = data.get("checkout")

        # Hotel property info
        hotel_obj = data.get("hotel") or {}
        hotel_id = hotel_obj.get("hotelId") if isinstance(hotel_obj, dict) else None
        hotel_name = hotel_obj.get("name") if isinstance(hotel_obj, dict) else None

        # Guest info
        holder_obj = data.get("holder") or {}
        guest_name = None
        guest_email = None
        if isinstance(holder_obj, dict):
            fn = holder_obj.get("firstName") or request.holder.first_name
            ln = holder_obj.get("lastName") or request.holder.last_name
            guest_name = f"{fn} {ln}".strip() or None
            guest_email = holder_obj.get("email") or request.holder.email
        else:
            guest_name = f"{request.holder.first_name} {request.holder.last_name}".strip()
            guest_email = request.holder.email

        # Price info
        price_obj = data.get("price") or {}
        if isinstance(price_obj, dict):
            total_price = float(price_obj.get("amount") or price_obj.get("total") or 0.0)
            currency = str(price_obj.get("currency") or "INR")
        elif isinstance(price_obj, (int, float)):
            total_price = float(price_obj)
            currency = "INR"
        else:
            total_price = None
            currency = "INR"

        canc_pol = data.get("cancellationPolicies")
        canc_str = None
        if isinstance(canc_pol, dict):
            canc_str = canc_pol.get("description") or canc_pol.get("policyText")
        elif isinstance(canc_pol, str):
            canc_str = canc_pol

        created_at = data.get("createdAt") or data.get("bookingDate")

        return HotelBookingConfirmationResponse(
            booking_id=booking_id,
            status=booking_status,
            hotel_confirmation_code=confirmation_code,
            checkin=checkin,
            checkout=checkout,
            hotel_id=hotel_id,
            hotel_name=hotel_name,
            guest_name=guest_name,
            guest_email=guest_email,
            total_price=total_price,
            currency=currency,
            cancellation_policy=canc_str,
            is_sandbox=nuitee_service.is_sandbox,
            created_at=created_at,
            raw_details=data,
        )

    except NuiteeConfigurationError as exc:
        logger.error("Hotel provider configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel booking provider is not configured.",
        )
    except NuiteeAuthenticationError as exc:
        logger.error("Hotel provider authentication error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hotel provider authentication failed.",
        )
    except NuiteeNetworkError as exc:
        logger.error("Hotel provider network error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Hotel booking provider connection timed out.",
        )
    except NuiteeResponseError as exc:
        logger.warning("Hotel provider booking error: %s", exc)
        msg = str(exc)
        if any(code in msg for code in ("HTTP 400", "HTTP 404", "HTTP 422")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hotel booking failed with provider: {msg}",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hotel booking execution error: {msg}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/hotels/{booking_id}",
    summary="Retrieve hotel booking details",
    response_model=HotelBookingConfirmationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Booking details retrieved successfully."},
        404: {"description": "Booking ID not found."},
        502: {"description": "Upstream LiteAPI error."},
        503: {"description": "Hotel booking provider not configured."},
        504: {"description": "Provider connection timed out."},
    },
)
def get_hotel_booking(
    booking_id: str,
    nuitee_service: NuiteeService = Depends(get_nuitee_service),
) -> HotelBookingConfirmationResponse:
    """Retrieve the current details and confirmation status of an existing booking."""
    logger.info("Retrieving booking details for booking_id: %s", booking_id)

    try:
        raw_res = nuitee_service.get_booking_details(booking_id=booking_id)

        data = raw_res.get("data") or {}
        if not data and isinstance(raw_res, dict):
            data = raw_res

        retrieved_id = data.get("bookingId") or data.get("booking_id")
        if not retrieved_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking '{booking_id}' not found.",
            )

        booking_status = data.get("status") or "UNKNOWN"
        confirmation_code = data.get("hotelConfirmationCode") or data.get("confirmationCode")
        checkin = data.get("checkin")
        checkout = data.get("checkout")

        hotel_obj = data.get("hotel") or {}
        hotel_id = hotel_obj.get("hotelId") if isinstance(hotel_obj, dict) else None
        hotel_name = hotel_obj.get("name") if isinstance(hotel_obj, dict) else None

        holder_obj = data.get("holder") or {}
        guest_name = None
        guest_email = None
        if isinstance(holder_obj, dict):
            fn = holder_obj.get("firstName") or ""
            ln = holder_obj.get("lastName") or ""
            guest_name = f"{fn} {ln}".strip() or None
            guest_email = holder_obj.get("email")

        price_obj = data.get("price") or {}
        if isinstance(price_obj, dict):
            total_price = float(price_obj.get("amount") or price_obj.get("total") or 0.0)
            currency = str(price_obj.get("currency") or "INR")
        elif isinstance(price_obj, (int, float)):
            total_price = float(price_obj)
            currency = "INR"
        else:
            total_price = None
            currency = "INR"

        canc_pol = data.get("cancellationPolicies")
        canc_str = None
        if isinstance(canc_pol, dict):
            canc_str = canc_pol.get("description") or canc_pol.get("policyText")
        elif isinstance(canc_pol, str):
            canc_str = canc_pol

        created_at = data.get("createdAt") or data.get("bookingDate")

        return HotelBookingConfirmationResponse(
            booking_id=retrieved_id,
            status=booking_status,
            hotel_confirmation_code=confirmation_code,
            checkin=checkin,
            checkout=checkout,
            hotel_id=hotel_id,
            hotel_name=hotel_name,
            guest_name=guest_name,
            guest_email=guest_email,
            total_price=total_price,
            currency=currency,
            cancellation_policy=canc_str,
            is_sandbox=nuitee_service.is_sandbox,
            created_at=created_at,
            raw_details=data,
        )

    except HTTPException:
        raise
    except NuiteeConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel booking provider is not configured.",
        )
    except NuiteeAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hotel provider authentication failed.",
        )
    except NuiteeNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Hotel booking provider connection timed out.",
        )
    except NuiteeResponseError as exc:
        msg = str(exc)
        if "HTTP 404" in msg or "not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking '{booking_id}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hotel booking provider error: {msg}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.post(
    "/hotels/{booking_id}/cancel",
    summary="Cancel hotel booking",
    response_model=HotelBookingCancellationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Hotel booking cancelled successfully."},
        400: {"description": "Booking cannot be cancelled under provider policy."},
        404: {"description": "Booking ID not found."},
        502: {"description": "Upstream LiteAPI error."},
        503: {"description": "Hotel booking provider not configured."},
        504: {"description": "Provider connection timed out."},
    },
)
def cancel_hotel_booking(
    booking_id: str,
    nuitee_service: NuiteeService = Depends(get_nuitee_service),
) -> HotelBookingCancellationResponse:
    """Cancel a confirmed hotel booking with LiteAPI."""
    logger.info("Requesting cancellation for booking_id: %s", booking_id)

    try:
        raw_res = nuitee_service.cancel_booking(booking_id=booking_id)

        data = raw_res.get("data") or {}
        if not data and isinstance(raw_res, dict):
            data = raw_res

        cancelled_id = data.get("bookingId") or data.get("booking_id") or booking_id
        canc_status = data.get("status") or "CANCELLED"
        fee = float(data.get("cancellationFee") or data.get("fee") or 0.0)
        refund = float(data.get("refundAmount") or data.get("refund") or 0.0)
        currency = str(data.get("currency") or "INR")
        message = data.get("message") or f"Booking {booking_id} cancellation processed."

        return HotelBookingCancellationResponse(
            booking_id=cancelled_id,
            status=canc_status,
            cancellation_fee=fee,
            refund_amount=refund,
            currency=currency,
            is_sandbox=nuitee_service.is_sandbox,
            message=message,
        )

    except NuiteeConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hotel booking provider is not configured.",
        )
    except NuiteeAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hotel provider authentication failed.",
        )
    except NuiteeNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Hotel booking provider connection timed out.",
        )
    except NuiteeResponseError as exc:
        msg = str(exc)
        if "HTTP 404" in msg or "not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking '{booking_id}' not found.",
            )
        if any(code in msg for code in ("HTTP 400", "HTTP 422")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cancellation rejected by hotel provider: {msg}",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hotel cancellation provider error: {msg}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

