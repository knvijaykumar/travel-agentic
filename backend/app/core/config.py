from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated using Pydantic."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General API Configuration
    PROJECT_NAME: str = "AI-Powered Virtual Travel Agent"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # CORS Configuration
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Amadeus Travel API (Accommodation & Transport)
    AMADEUS_CLIENT_ID: str = ""
    AMADEUS_CLIENT_SECRET: str = ""
    AMADEUS_HOSTNAME: str = "test.api.amadeus.com"

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Ignav Flight API Configuration
    IGNAV_API_KEY: str = ""
    IGNAV_BASE_URL: str = "https://ignav.com/api"

    # Nuitee Connect (LiteAPI) Hotel API Configuration
    NUITEE_API_KEY: str = ""
    NUITEE_BASE_URL: str = "https://api.liteapi.travel/v3.0"
    NUITEE_BOOK_BASE_URL: str = "https://book.liteapi.travel/v3.0"

    # Geoapify Places & Geocoding API
    GEOAPIFY_API_KEY: str = ""

    # Routing & Mapping
    OSRM_BASE_URL: str = "https://router.project-osrm.org"

    # Mock vs Live API Strategy
    USE_MOCK_DATA: bool = True


settings = Settings()

