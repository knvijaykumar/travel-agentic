import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.schemas.place import Place
from backend.app.services.clip_service import CLIPService, get_clip_service
from backend.app.services.geoapify_service import GeoapifyService
from backend.app.services.wikimedia_service import WikimediaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places", tags=["Places"])

_geoapify_service: Optional[GeoapifyService] = None
_wikimedia_service: Optional[WikimediaService] = None


def get_geoapify_service() -> GeoapifyService:
    """Dependency providing the GeoapifyService instance."""
    global _geoapify_service
    if _geoapify_service is None:
        _geoapify_service = GeoapifyService()
    return _geoapify_service


def get_wikimedia_service() -> WikimediaService:
    """Dependency providing the WikimediaService instance."""
    global _wikimedia_service
    if _wikimedia_service is None:
        _wikimedia_service = WikimediaService()
    return _wikimedia_service


def build_place_description(
    place: Place,
    city: Optional[str] = None,
    region: Optional[str] = None,
) -> str:
    """Build a natural descriptive text prompt for CLIP scoring based on place attributes."""
    clean_name = place.name.strip()
    clean_category = place.category.replace(".", " ").replace("_", " ").strip()

    loc_parts = []
    if city and city.strip():
        loc_parts.append(city.strip())
    if region and region.strip() and (not city or city.strip().lower() != region.strip().lower()):
        loc_parts.append(region.strip())
    if place.country and place.country.strip():
        loc_parts.append(place.country.strip())

    loc_str = f" in {', '.join(loc_parts)}" if loc_parts else ""
    cat_str = f", a {clean_category}" if clean_category else ""

    return f"A photo of {clean_name}{cat_str}{loc_str}"


def enrich_places_with_images(
    places: List[Place],
    wikimedia_service: WikimediaService,
    clip_service: Optional[CLIPService] = None,
    max_workers: int = 5,
    candidates_limit: int = 3,
) -> List[Place]:
    """Enrich a list of Place objects with Wikimedia images using CLIP ranking."""
    if not places:
        return []

    # Phase 1: Fetch candidate images concurrently (I/O bound)
    def _fetch_candidates_for_place(place: Place):
        city = place.city
        region = None
        if place.address:
            addr_lower = place.address.lower()
            for r_candidate in ["goa", "karnataka", "maharashtra", "kerala", "tamil nadu", "delhi", "rajasthan"]:
                if r_candidate in addr_lower and (not city or city.lower() != r_candidate):
                    region = r_candidate.title()
                    break

        candidates = None
        try:
            cand_res = wikimedia_service.get_candidates(
                place_name=place.name,
                city=city,
                region=region,
                limit=candidates_limit,
            )
            if isinstance(cand_res, list):
                candidates = cand_res
        except Exception as exc:
            logger.warning(f"Failed to fetch Wikimedia candidates for '{place.name}': {exc}")
            candidates = None

        if candidates is None:
            try:
                image_data = wikimedia_service.get_image(
                    place_name=place.name,
                    city=city,
                    region=region,
                )
                candidates = [image_data] if image_data else []
            except Exception as exc:
                logger.warning(f"Failed to fetch Wikimedia image for '{place.name}': {exc}")
                candidates = []

        valid_cands = [c for c in candidates if isinstance(c, dict) and c.get("image_url")]
        return place, city, region, valid_cands

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fetched_results = list(executor.map(_fetch_candidates_for_place, places))

    # Phase 2: Disambiguate and rank candidates with CLIP (CPU bound)
    enriched_places: List[Place] = []
    for place, city, region, candidates in fetched_results:
        if not candidates:
            enriched_places.append(place)
            continue

        selected_candidate = None

        clip_available = clip_service is not None and bool(getattr(clip_service, "is_available", True))

        if clip_available and len(candidates) > 1:
            try:
                description = build_place_description(place, city=city, region=region)
                candidate_urls = [c["image_url"] for c in candidates]
                scores = clip_service.compute_batch_similarity(
                    images=candidate_urls,
                    text=description,
                )
                if scores and len(scores) == len(candidates):
                    valid_pairs = [
                        (cand, score)
                        for cand, score in zip(candidates, scores)
                        if score is not None
                    ]
                    if valid_pairs:
                        valid_pairs.sort(key=lambda x: x[1], reverse=True)
                        selected_candidate = valid_pairs[0][0]
                    else:
                        # All candidate images were invalid or unreadable
                        selected_candidate = None
                else:
                    # Incomplete/empty scores returned -> fallback to first candidate
                    selected_candidate = candidates[0]
            except Exception as exc:
                logger.warning(f"CLIP scoring failed for '{place.name}': {exc}. Falling back to default candidate.")
                selected_candidate = candidates[0]
        elif clip_available and len(candidates) == 1:
            try:
                description = build_place_description(place, city=city, region=region)
                scores = clip_service.compute_batch_similarity(
                    images=[candidates[0]["image_url"]],
                    text=description,
                )
                if scores and scores[0] is not None:
                    selected_candidate = candidates[0]
                elif scores and scores[0] is None:
                    # Single image was invalid/unreadable
                    selected_candidate = None
                else:
                    selected_candidate = candidates[0]
            except Exception as exc:
                logger.warning(f"CLIP scoring failed for '{place.name}': {exc}. Falling back to default candidate.")
                selected_candidate = candidates[0]
        else:
            # CLIP service not available: graceful fallback to top candidate
            selected_candidate = candidates[0]

        if selected_candidate and selected_candidate.get("image_url"):
            enriched_places.append(
                place.model_copy(
                    update={
                        "image_url": selected_candidate.get("image_url"),
                        "image_attribution": selected_candidate.get("attribution"),
                    }
                )
            )
        else:
            enriched_places.append(place)

    return enriched_places


@router.get(
    "/search",
    response_model=List[Place],
    status_code=status.HTTP_200_OK,
    summary="Search places by category and coordinates",
)
def search_places(
    category: str = Query(..., min_length=1, description="Category of places to search"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)"),
    radius_meters: int = Query(5000, gt=0, description="Search radius in meters (default 5000)"),
    limit: int = Query(20, gt=0, le=20, description="Max results (default 20, max 20)"),
    geoapify_service: GeoapifyService = Depends(get_geoapify_service),
    wikimedia_service: WikimediaService = Depends(get_wikimedia_service),
    clip_service: CLIPService = Depends(get_clip_service),
) -> List[Place]:
    """Search for places within a radius circle using Geoapify and enrich with Wikimedia images."""
    if not category.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category cannot be empty or whitespace.",
        )

    try:
        places = geoapify_service.search_places(
            category=category.strip(),
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider error: {str(exc)}",
        )

    if not places:
        return []

    return enrich_places_with_images(
        places,
        wikimedia_service=wikimedia_service,
        clip_service=clip_service,
        max_workers=5,
    )
