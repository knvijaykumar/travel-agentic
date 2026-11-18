from datetime import date
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class HotelSearchRequest(BaseModel):
    """Pydantic v2 schema for hotel search request validation."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    # Location filters (at least one valid strategy required, no conflicts)
    city_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("city_name", "cityName"),
        description="City name for location-based search (e.g. 'Mumbai')",
    )
    country_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("country_code", "countryCode"),
        description="2-letter ISO country code required with city_name (e.g. 'IN')",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude for coordinate-based search (-90.0 to 90.0)",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude for coordinate-based search (-180.0 to 180.0)",
    )
    radius: Optional[int] = Field(
        default=None,
        description="Search radius in kilometers for coordinate search (e.g. 10)",
    )
    hotel_ids: Optional[List[str]] = Field(
        default=None,
        validation_alias=AliasChoices("hotel_ids", "hotelIds"),
        description="List of specific hotel IDs to query",
    )

    # Dates
    checkin: str = Field(
        ...,
        validation_alias=AliasChoices("checkin", "check_in"),
        description="Check-in date formatted as YYYY-MM-DD",
        examples=["2026-12-20"],
    )
    checkout: str = Field(
        ...,
        validation_alias=AliasChoices("checkout", "check_out"),
        description="Check-out date formatted as YYYY-MM-DD",
        examples=["2026-12-22"],
    )

    # Guests & Occupancy
    adults: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Number of adult guests (1-20)",
    )
    children: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="Number of children (int) or list of child ages (0-17)",
    )
    occupancies: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional explicit room occupancy list for advanced multi-room queries",
    )

    # Pricing & Locale
    currency: str = Field(
        default="INR",
        description="3-letter currency code (default: 'INR')",
        examples=["INR"],
    )
    guest_nationality: str = Field(
        default="IN",
        validation_alias=AliasChoices("guest_nationality", "guestNationality"),
        description="2-letter ISO country code of guest nationality (default: 'IN')",
        examples=["IN"],
    )

    @field_validator("checkin", "checkout", mode="before")
    @classmethod
    def validate_date_format(cls, v: Any) -> str:
        if isinstance(v, date):
            return v.isoformat()
        if not isinstance(v, str):
            raise ValueError("Date must be a string formatted as YYYY-MM-DD.")
        clean = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean):
            raise ValueError("Date must be formatted as YYYY-MM-DD.")
        try:
            date.fromisoformat(clean)
        except ValueError:
            raise ValueError("Date must be a valid calendar date formatted as YYYY-MM-DD.")
        return clean

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0.")
        return v

    @field_validator("radius")
    @classmethod
    def validate_radius(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Radius must be greater than 0.")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", clean):
            raise ValueError("Currency must be a valid 3-letter ISO code (e.g., 'INR', 'USD').")
        return clean

    @field_validator("guest_nationality")
    @classmethod
    def validate_guest_nationality(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{2}$", clean):
            raise ValueError("guest_nationality must be a valid 2-letter ISO country code (e.g., 'IN').")
        return clean

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().upper()
        if not clean:
            return None
        if not re.match(r"^[A-Z]{2}$", clean):
            raise ValueError("country_code must be a valid 2-letter ISO country code (e.g., 'IN').")
        return clean

    @field_validator("city_name")
    @classmethod
    def validate_city_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip()
        return clean if clean else None

    @field_validator("hotel_ids")
    @classmethod
    def validate_hotel_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        clean_ids = [i.strip() for i in v if isinstance(i, str) and i.strip()]
        if not clean_ids:
            raise ValueError("hotel_ids cannot be empty if specified.")
        return clean_ids

    @field_validator("children", mode="before")
    @classmethod
    def validate_children(cls, v: Any) -> Optional[List[int]]:
        if v is None:
            return None
        if isinstance(v, bool):
            raise ValueError("children cannot be a boolean.")
        if isinstance(v, int):
            if v < 0:
                raise ValueError("Number of children cannot be negative.")
            if v > 10:
                raise ValueError("Maximum 10 children allowed.")
            return [7] * v
        if isinstance(v, list):
            if len(v) > 10:
                raise ValueError("Maximum 10 children allowed.")
            validated = []
            for item in v:
                if isinstance(item, bool) or not isinstance(item, int):
                    raise ValueError("Child age must be an integer between 0 and 17.")
                if not (0 <= item <= 17):
                    raise ValueError("Child age must be between 0 and 17.")
                validated.append(item)
            return validated
        raise ValueError("children must be an integer count or a list of child ages.")

    @model_validator(mode="after")
    def validate_locations_and_dates(self) -> "HotelSearchRequest":
        # 1. Date check
        d_in = date.fromisoformat(self.checkin)
        d_out = date.fromisoformat(self.checkout)
        if d_out <= d_in:
            raise ValueError("Check-out date must be after check-in date.")

        # 2. Check location filters
        has_city = bool(self.city_name)
        has_country = bool(self.country_code)
        has_lat = self.latitude is not None
        has_lon = self.longitude is not None
        has_hotel_ids = bool(self.hotel_ids)

        if has_city and not has_country:
            raise ValueError("country_code is required when city_name is provided.")
        if has_country and not has_city:
            raise ValueError("city_name is required when country_code is provided.")

        if has_lat and not has_lon:
            raise ValueError("Both latitude and longitude must be provided for coordinate search.")
        if has_lon and not has_lat:
            raise ValueError("Both latitude and longitude must be provided for coordinate search.")

        if self.radius is not None and not (has_lat and has_lon):
            raise ValueError("radius can only be specified when latitude and longitude are provided.")

        is_city_filter = has_city and has_country
        is_coord_filter = has_lat and has_lon
        is_hotel_id_filter = has_hotel_ids

        active_filters = sum([is_city_filter, is_coord_filter, is_hotel_id_filter])
        if active_filters == 0:
            raise ValueError(
                "At least one location filter is required: (city_name + country_code), (latitude + longitude), or hotel_ids."
            )
        if active_filters > 1:
            raise ValueError(
                "Conflicting location parameters: please provide only one of (city_name + country_code), (latitude + longitude), or hotel_ids."
            )

        return self

    def to_occupancies(self) -> List[Dict[str, Any]]:
        """Convert adults and children or explicit occupancies into LiteAPI format."""
        if self.occupancies:
            return self.occupancies
        children_list = self.children if isinstance(self.children, list) else []
        return [{"adults": self.adults, "children": children_list}]

