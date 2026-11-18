from typing import List, Optional
from pydantic import BaseModel, Field


class TravelIntentDraft(BaseModel):
    """Pydantic model representing partially or fully extracted travel intent from natural language.

    All fields are strictly optional (defaulting to None or empty list) to accommodate
    incomplete user inputs without inventing assumptions or enforcing defaults.
    """

    destination: Optional[str] = Field(
        default=None,
        description="Target destination mentioned by user, or None if unstated",
    )
    duration_days: Optional[int] = Field(
        default=None,
        description="Duration of the trip in days, or None if unstated",
    )
    travellers: Optional[int] = Field(
        default=None,
        description="Number of people travelling, or None if unstated",
    )
    budget: Optional[float] = Field(
        default=None,
        description="Budget amount, or None if unstated",
    )
    currency: Optional[str] = Field(
        default=None,
        description="Currency code (e.g. INR, USD, EUR), or None if unstated",
    )
    interests: List[str] = Field(
        default_factory=list,
        description="List of activities, vibes, or interests mentioned by the user",
    )
    departure_city: Optional[str] = Field(
        default=None,
        description="Origin or departure city, or None if unstated",
    )
    travel_date: Optional[str] = Field(
        default=None,
        description="Specific date, month, or season mentioned, or None if unstated",
    )
    skipped_fields: List[str] = Field(
        default_factory=list,
        description="List of fields explicitly skipped, declined, or deferred by the user",
    )

    @property
    def is_complete(self) -> bool:
        """Helper to determine whether all mandatory fields for a full TravelRequest are present."""
        return (
            self.destination is not None
            and self.duration_days is not None
            and self.duration_days > 0
            and self.travellers is not None
            and self.travellers > 0
            and self.budget is not None
            and self.budget > 0
        )

