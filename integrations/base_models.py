from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    LIVE_API = "live_api"
    MOCK_FIXTURE = "mock_fixture"
    FALLBACK = "fallback"


T = TypeVar("T")


class IntegrationMetadata(BaseModel):
    """Metadata tracking data provenance to ensure mock data is never disguised as live."""
    source_name: str
    data_source_type: DataSourceType
    is_mock: bool
    status_code: int = 200
    error_message: Optional[str] = None
    cached: bool = False


class IntegrationResponse(BaseModel, Generic[T]):
    """Standardized response container for all external integrations."""
    success: bool
    data: T
    metadata: IntegrationMetadata
