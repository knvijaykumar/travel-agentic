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
from backend.app.schemas.place import Place

logger = logging.getLogger(__name__)

GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"


class GeoapifyService:
    """Service to search places and attractions using Geoapify Places API."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = settings.GEOAPIFY_API_KEY or os.getenv("GEOAPIFY_API_KEY")
            if not api_key:
                env_file = Path(__file__).resolve().parents[2] / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                api_key = os.getenv("GEOAPIFY_API_KEY")
        self._api_key = api_key or ""

    def search_places(
        self,
        category: str,
        latitude: float,
        longitude: float,
        radius_meters: int = 5000,
        limit: int = 20,
        timeout: int = 15,
    ) -> List[Place]:
        """Search places within a circular radius around (latitude, longitude)."""
        if not self._api_key:
            logger.warning("GEOAPIFY_API_KEY is not configured; returning empty list.")
            return []

        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            logger.warning(f"Invalid coordinates: lat={latitude}, lon={longitude}")
            return []

        params = {
            "categories": category,
            "filter": f"circle:{longitude},{latitude},{radius_meters}",
            "limit": str(limit),
            "apiKey": self._api_key,
        }

        url = f"{GEOAPIFY_PLACES_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TravelAgent/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            logger.error(f"Geoapify HTTP error: {exc.code} {exc.reason}")
            return []
        except urllib.error.URLError as exc:
            logger.error(f"Geoapify network error: {exc.reason}")
            return []
        except TimeoutError:
            logger.error("Geoapify request timed out")
            return []
        except Exception as exc:
            logger.error(f"Unexpected Geoapify error: {exc}")
            return []

        features = data.get("features", [])
        if not features:
            return []

        places: List[Place] = []
        for idx, feat in enumerate(features, start=1):
            place = self._parse_feature(feat, fallback_category=category, default_id=f"geo_{idx}")
            if place:
                places.append(place)

        return places

    def _parse_feature(
        self,
        feature: dict,
        fallback_category: str,
        default_id: str,
    ) -> Optional[Place]:
        """Convert a GeoJSON feature dictionary into a validated Place object."""
        if not isinstance(feature, dict):
            return None

        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []

        # Extract latitude and longitude
        lat = props.get("lat")
        lon = props.get("lon")

        if (lat is None or lon is None) and len(coords) >= 2:
            lon = coords[0]
            lat = coords[1]

        if lat is None or lon is None:
            return None

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return None

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None

        name = props.get("name") or props.get("address_line1") or props.get("formatted")
        if not name or not str(name).strip():
            name = f"Unnamed {fallback_category.split('.')[-1].capitalize()}"

        place_id = str(props.get("place_id") or feature.get("id") or default_id).strip()

        categories = props.get("categories") or []
        cat = categories[0] if categories and isinstance(categories, list) else fallback_category

        address = props.get("formatted") or props.get("address_line2")
        city = props.get("city")
        country = props.get("country")

        try:
            return Place(
                place_id=place_id,
                name=str(name).strip(),
                category=str(cat).strip(),
                latitude=lat,
                longitude=lon,
                address=str(address).strip() if address else None,
                city=str(city).strip() if city else None,
                country=str(country).strip() if country else None,
                image_url=None,
                image_attribution=None,
                source_provider="Geoapify",
            )
        except Exception as exc:
            logger.warning(f"Place validation skipped: {exc}")
            return None

    def geocode_city(
        self,
        city: str,
        country: Optional[str] = None,
        timeout: int = 15,
    ) -> Optional[Dict[str, Any]]:
        """Geocode a city or destination name into latitude and longitude coordinates.

        Args:
            city: Destination or city name (e.g. 'Goa', 'Jaipur', 'Bengaluru').
            country: Optional country name or code to disambiguate (e.g. 'India' or 'IN').
            timeout: Network request timeout in seconds (default: 15).

        Returns:
            Dictionary with keys 'latitude', 'longitude', 'lat', 'lon', 'city', 'country', 'formatted',
            or None if geocoding failed or city was not found.
        """
        if not self._api_key:
            logger.warning("GEOAPIFY_API_KEY is not configured; returning None.")
            return None

        if not city or not city.strip():
            logger.warning("Empty city passed to geocode_city; returning None.")
            return None

        clean_city = city.strip()
        search_text = f"{clean_city}, {country.strip()}" if country and country.strip() else clean_city

        params = {
            "text": search_text,
            "apiKey": self._api_key,
            "limit": "1",
            "format": "json",
        }

        url = f"{GEOAPIFY_GEOCODE_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TravelAgent/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)
        except urllib.error.HTTPError as exc:
            logger.error(f"Geoapify geocoding HTTP error: {exc.code} {exc.reason}")
            return None
        except urllib.error.URLError as exc:
            logger.error(f"Geoapify geocoding network error: {exc.reason}")
            return None
        except TimeoutError:
            logger.error("Geoapify geocoding request timed out")
            return None
        except Exception as exc:
            logger.error(f"Unexpected Geoapify geocoding error: {exc}")
            return None

        return self._parse_geocode_result(data, fallback_city=clean_city)

    geocode_destination = geocode_city

    def _parse_geocode_result(
        self,
        data: dict,
        fallback_city: str,
    ) -> Optional[Dict[str, Any]]:
        """Extract and validate coordinates and location metadata from Geoapify geocoding payload."""
        if not isinstance(data, dict):
            return None

        # Format 1: format=json -> results list
        items = data.get("results")
        # Format 2: GeoJSON -> features list
        if items is None:
            items = data.get("features")

        if not items or not isinstance(items, list) or len(items) == 0:
            return None

        first = items[0]
        if not isinstance(first, dict):
            return None

        props = first.get("properties") if "properties" in first else first
        geometry = first.get("geometry") or {}
        coords = geometry.get("coordinates") or []

        lat = props.get("lat")
        lon = props.get("lon")

        if (lat is None or lon is None) and len(coords) >= 2:
            lon = coords[0]
            lat = coords[1]

        if lat is None or lon is None:
            return None

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return None

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None

        res_city = props.get("city") or props.get("name") or fallback_city
        res_country = props.get("country")
        formatted = props.get("formatted") or (f"{res_city}, {res_country}" if res_country else res_city)

        return {
            "latitude": lat,
            "longitude": lon,
            "lat": lat,
            "lon": lon,
            "city": str(res_city).strip(),
            "country": str(res_country).strip() if res_country else None,
            "formatted": str(formatted).strip(),
            "place_id": str(props.get("place_id") or "").strip() or None,
        }
