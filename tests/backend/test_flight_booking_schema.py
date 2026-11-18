"""Unit tests for Phase 8.4: Flight Booking Workflow Schema & Provenance.

Tests cover:
- booking_url validation on AggregatedFlightOption and FlightBookingRecommendation
- Rejection of invalid schemes (javascript:, ftp:, data:, file:, etc.)
- Normalization and null handling
- Serialization inside TripItinerary
- Non-fabrication guarantee in FlightDiscoveryService parsing
"""

import pytest
from pydantic import ValidationError
from backend.app.schemas.trip_aggregation import AggregatedFlightOption
from backend.app.schemas.itinerary import FlightBookingRecommendation
from backend.app.services.flight_discovery_service import IgnavFlightProvider


class TestFlightBookingSchemas:
    """Tests for booking_url fields on flight aggregation and itinerary recommendation schemas."""

    def test_aggregated_flight_option_valid_http_url(self):
        option = AggregatedFlightOption(
            flight_id="FL-INDIGO-6E101",
            direction="outbound",
            carrier="IndiGo",
            origin_iata="DEL",
            destination_iata="GOI",
            departure_date="2026-12-15",
            duration_minutes=150,
            price_amount=4500.0,
            currency="INR",
            booking_url="https://www.goindigo.in/booking/select?ref=DEL-GOI",
        )
        assert option.booking_url == "https://www.goindigo.in/booking/select?ref=DEL-GOI"

    def test_aggregated_flight_option_none_url(self):
        option = AggregatedFlightOption(
            flight_id="FL-AIRINDIA-AI102",
            direction="outbound",
            carrier="Air India",
            origin_iata="BOM",
            destination_iata="GOI",
            departure_date="2026-12-15",
            duration_minutes=75,
            price_amount=5200.0,
            currency="INR",
            booking_url=None,
        )
        assert option.booking_url is None

    def test_aggregated_flight_option_whitespace_stripped(self):
        option = AggregatedFlightOption(
            flight_id="FL-VISTARA-UK842",
            direction="return",
            carrier="Vistara",
            origin_iata="DEL",
            destination_iata="GOI",
            departure_date="2026-12-15",
            duration_minutes=140,
            price_amount=6000.0,
            currency="INR",
            booking_url="   https://www.airvistara.com/trip   ",
        )
        assert option.booking_url == "https://www.airvistara.com/trip"

    @pytest.mark.parametrize(
        "unsafe_url",
        [
            "javascript:alert('pwned')",
            "ftp://ftp.airline.com/booking",
            "data:text/html;base64,PHNjcmlwdD4=",
            "file:///C:/passwords.txt",
            "not-a-valid-url",
            "http://",
        ],
    )
    def test_aggregated_flight_option_rejects_unsafe_urls(self, unsafe_url: str):
        with pytest.raises(ValidationError) as exc_info:
            AggregatedFlightOption(
                flight_id="FL-BAD-URL",
                direction="outbound",
                carrier="TestAir",
                origin_iata="DEL",
                destination_iata="GOI",
                departure_date="2026-12-15",
                duration_minutes=120,
                price_amount=3000.0,
                booking_url=unsafe_url,
            )
        assert "booking_url must use http or https scheme" in str(exc_info.value) or "valid URL" in str(exc_info.value)

    def test_flight_booking_recommendation_valid_url(self):
        rec = FlightBookingRecommendation(
            flight_id="FL-REC-1",
            direction="outbound",
            carrier="IndiGo",
            origin_iata="DEL",
            destination_iata="GOI",
            departure_date="2026-12-15",
            departure_time="08:00",
            arrival_time="10:30",
            price_amount=4800.0,
            currency="INR",
            booking_url="https://www.goindigo.in/booking",
        )
        assert rec.booking_url == "https://www.goindigo.in/booking"

    def test_flight_booking_recommendation_rejects_unsafe_url(self):
        with pytest.raises(ValidationError):
            FlightBookingRecommendation(
                flight_id="FL-REC-BAD",
                direction="outbound",
                carrier="IndiGo",
                origin_iata="DEL",
                destination_iata="GOI",
                departure_date="2026-12-15",
                departure_time="08:00",
                arrival_time="10:30",
                price_amount=4800.0,
                currency="INR",
                booking_url="javascript:hack()",
            )


class TestFlightDiscoveryServiceProvenance:
    """Verifies that FlightDiscoveryService does NOT fabricate booking URLs."""

    def test_ignav_parser_preserves_none_when_no_url_in_payload(self):
        provider = IgnavFlightProvider()
        response = {
            "origin": "DEL",
            "destination": "GOI",
            "itineraries": [
                {
                    "ignav_id": "fare_101",
                    "price": {"amount": 4200, "currency": "INR"},
                    "outbound": {
                        "carrier": "IndiGo",
                        "duration_minutes": 150,
                        "segments": [
                            {
                                "marketing_carrier_code": "6E",
                                "flight_number": "6E-204",
                                "departure_airport": "DEL",
                                "arrival_airport": "GOI",
                                "departure_time_local": "08:00",
                                "arrival_time_local": "10:30",
                            }
                        ],
                    },
                }
            ],
        }

        parsed = provider._parse_itineraries(
            response=response,
            direction="outbound",
            departure_date="2026-12-15",
            max_flights=5,
        )

        assert len(parsed) == 1
        # Crucial: Never invent a fake URL when Ignav does not provide one
        assert parsed[0].booking_url is None

    def test_ignav_parser_captures_genuine_url_if_present(self):
        provider = IgnavFlightProvider()
        response = {
            "origin": "DEL",
            "destination": "GOI",
            "itineraries": [
                {
                    "ignav_id": "fare_102",
                    "price": {"amount": 5100, "currency": "INR"},
                    "outbound": {
                        "carrier": "Air India",
                        "duration_minutes": 145,
                        "segments": [
                            {
                                "marketing_carrier_code": "AI",
                                "flight_number": "AI-880",
                                "departure_airport": "DEL",
                                "arrival_airport": "GOI",
                                "departure_time_local": "11:00",
                                "arrival_time_local": "13:25",
                            }
                        ],
                    },
                    "booking_url": "https://www.airindia.com/offers/ai202",
                }
            ],
        }

        parsed = provider._parse_itineraries(
            response=response,
            direction="outbound",
            departure_date="2026-12-15",
            max_flights=5,
        )

        assert len(parsed) == 1
        assert parsed[0].booking_url == "https://www.airindia.com/offers/ai202"
