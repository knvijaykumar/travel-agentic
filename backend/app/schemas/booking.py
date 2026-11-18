import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class HotelGuestHolder(BaseModel):
    """Guest holder contact details required for LiteAPI hotel booking."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Guest first given name",
        examples=["Jane"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=60,
        description="Guest last family name",
        examples=["Doe"],
    )
    email: str = Field(
        ...,
        description="Primary contact email address for booking confirmation",
        examples=["jane.doe@example.com"],
    )
    phone: Optional[str] = Field(
        default=None,
        description="Optional contact telephone number with country code",
        examples=["+919876543210"],
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Name cannot be empty or whitespace only.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip()
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, clean):
            raise ValueError("A valid email address is required.")
        return clean

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        return clean if clean else None


class HotelPrebookRequest(BaseModel):
    """Request schema to pre-book a selected hotel rate offer."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    offer_id: str = Field(
        ...,
        min_length=1,
        description="Unique rate offer ID from LiteAPI hotel search results",
        examples=["offer_xyz12345"],
    )
    use_payment_sdk: bool = Field(
        default=False,
        description="Whether payment collection will use LiteAPI client-side SDK",
    )

    @field_validator("offer_id")
    @classmethod
    def validate_offer_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("offer_id cannot be empty.")
        return clean


class HotelPrebookResponse(BaseModel):
    """Normalized response schema returned after pre-booking a hotel rate."""

    prebook_id: str = Field(..., description="Unique prebook session ID from LiteAPI")
    offer_id: str = Field(..., description="The offer ID that was pre-booked")
    price_amount: float = Field(..., description="Locked total price amount")
    currency: str = Field(default="INR", description="Price currency code")
    cancellation_policy: Optional[str] = Field(
        default=None,
        description="Human-readable cancellation policy summary",
    )
    room_name: Optional[str] = Field(
        default=None,
        description="Room description or name locked in this pre-book",
    )
    is_sandbox: bool = Field(
        default=True,
        description="True if booked against LiteAPI sandbox environment",
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw upstream prebook response payload (for debugging/audit)",
    )


class HotelBookingConfirmationRequest(BaseModel):
    """Request schema to explicitly confirm a hotel booking with guest information."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    prebook_id: str = Field(
        ...,
        min_length=1,
        description="Valid prebookId obtained from the /hotels/prebook step",
        examples=["pb_abc98765"],
    )
    holder: HotelGuestHolder = Field(
        ...,
        description="Contact and identity details of the primary guest",
    )
    client_reference: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional internal correlation ID or itinerary reference",
        examples=["VTA-TRIP-2026-GOA"],
    )
    payment_method: Optional[str] = Field(
        default="ACC_CREDIT_CARD",
        description="Payment method identifier (e.g., 'ACC_CREDIT_CARD' for sandbox)",
    )

    @field_validator("prebook_id")
    @classmethod
    def validate_prebook_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("prebook_id cannot be empty.")
        return clean


class HotelBookingConfirmationResponse(BaseModel):
    """Normalized response schema for a confirmed hotel booking."""

    booking_id: str = Field(..., description="Unique provider booking identifier")
    status: str = Field(..., description="Booking status (e.g. 'CONFIRMED', 'PENDING')")
    hotel_confirmation_code: Optional[str] = Field(
        default=None,
        description="Hotel confirmation reference code",
    )
    checkin: Optional[str] = Field(default=None, description="Check-in date (YYYY-MM-DD)")
    checkout: Optional[str] = Field(default=None, description="Check-out date (YYYY-MM-DD)")
    hotel_id: Optional[str] = Field(default=None, description="Hotel identifier")
    hotel_name: Optional[str] = Field(default=None, description="Hotel property name")
    guest_name: Optional[str] = Field(default=None, description="Full name of primary guest")
    guest_email: Optional[str] = Field(default=None, description="Email address of primary guest")
    total_price: Optional[float] = Field(default=None, description="Total booking price")
    currency: str = Field(default="INR", description="Currency code")
    cancellation_policy: Optional[str] = Field(
        default=None,
        description="Cancellation terms and deadlines",
    )
    is_sandbox: bool = Field(
        default=True,
        description="True if booked against LiteAPI sandbox environment",
    )
    created_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the booking was confirmed",
    )
    raw_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw upstream confirmation payload (for debugging/audit)",
    )


class HotelBookingCancellationResponse(BaseModel):
    """Normalized response schema returned when a hotel booking is cancelled."""

    booking_id: str = Field(..., description="The booking ID that was cancelled")
    status: str = Field(..., description="Updated status, e.g. 'CANCELLED'")
    cancellation_fee: float = Field(default=0.0, description="Cancellation fee charged")
    refund_amount: float = Field(default=0.0, description="Refund amount processed")
    currency: str = Field(default="INR", description="Currency code")
    is_sandbox: bool = Field(
        default=True,
        description="True if processed in LiteAPI sandbox environment",
    )
    message: Optional[str] = Field(
        default=None,
        description="Informational cancellation message",
    )

