import html
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

WIKIMEDIA_COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
DEFAULT_USER_AGENT = "VirtualTravelAgent/1.0 (https://github.com/travel-agentic; contact: admin@travelagentic.local)"
VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".svg")

# Common generic categories, POI types, and grammatical stopwords to filter out
GENERIC_STOP_WORDS: Set[str] = {
    "museum", "hotel", "resort", "restaurant", "cafe", "bar", "park",
    "garden", "fort", "palace", "temple", "church", "cathedral", "monument",
    "memorial", "smarak", "bhavan", "bhawan", "sthal", "stala", "stupa",
    "beach", "island", "bridge", "tower", "center", "centre", "mall",
    "shop", "store", "point", "spot", "spots", "station", "complex",
    "building", "house", "villa", "lake", "river", "view", "port",
    "car", "vintage", "world", "gallery", "mandir", "masjid", "dargah",
    "gurudwara", "gurdwara", "ashram", "chowk",
    "the", "a", "an", "and", "or", "of", "in", "at", "to", "for", "on",
    "by", "with", "from", "de", "la", "le", "el", "near",
}

# Generic geographic / administrative terms
LOCATION_WORDS: Set[str] = {
    "goa", "india", "state", "district", "north", "south", "east", "west",
    "central", "city", "town", "village",
}

# File title prefixes and file extensions
FILE_PREFIX_EXTENSIONS: Set[str] = {
    "file", "image", "jpg", "jpeg", "png", "webp", "svg", "gif", "tif", "tiff",
}

# Common attraction qualifiers that are not distinctive proper nouns
COMMON_QUALIFIERS: Set[str] = {
    "wax", "art", "arts", "modern", "national", "state", "royal", "grand",
    "central", "public", "peace", "war", "science", "railway", "botanical",
    "zoological", "historic", "historical", "ancient", "city", "tribal",
    "craft", "crafts", "doll", "dolls", "toy", "toys", "children", "childrens",
    "aviation", "military", "naval", "maritime", "space", "natural", "history",
    "planetarium", "aquarium", "zoo", "wildlife", "safari", "cultural", "folk",
    "technology", "technological", "police", "shahid", "shaheed", "martyr", "martyrs",
    "archiepiscopal", "episcopal", "diocesan", "patriarchal", "metropolitan",
    "apostolic", "papal", "pontifical", "basilica", "parish",
}

# Common photo and architectural feature words that should not be flagged as conflicting locations
PHOTO_DESCRIPTIVE_WORDS: Set[str] = {
    "view", "views", "photo", "image", "picture", "front", "interior", "exterior",
    "entrance", "side", "night", "aerial", "panorama", "panoramic", "closeup",
    "detail", "details", "inside", "outside", "building", "facade", "gate", "hall",
    "sign", "board", "display", "statue", "exhibit", "room", "arch", "wall", "walls",
    "roof", "day", "sunset", "sunrise", "sky", "street", "road", "main", "old", "new",
    "bastion", "rampart", "ramparts", "lighthouse", "courtyard", "stairs", "steps",
    "ruins", "remains", "cannon", "cannons", "altar", "scenery", "scenic", "landscape",
    "overview", "complex", "compound", "pillar", "cross", "nave",
    "background", "foreground", "iconic", "cenotaph", "cenotaphs",
    "distance", "evening", "morning", "dusk", "dawn", "summer", "winter", "spring",
    "autumn", "monsoon", "sunny", "rainy", "cloudy", "cloud", "clouds",
}

# Media / photographic terms that precede 'of' to describe photo subject (not geographic location)
MEDIA_PREFIX_WORDS: Set[str] = {
    "view", "views", "photo", "image", "picture", "photograph", "panorama",
    "panoramic", "statue", "portrait", "painting", "drawing", "illustration",
    "exterior", "interior", "facade", "front", "rear", "back", "side",
    "entrance", "gate", "room", "aerial", "closeup", "detail", "details",
}

# Major regional / state administrative names
MAJOR_REGIONS: Set[str] = {
    "gujarat", "maharashtra", "karnataka", "rajasthan", "kerala", "telangana",
    "punjab", "haryana", "bengal", "bihar", "odisha", "orissa", "assam",
    "kashmir", "delhi", "goa", "andhra", "tamil", "nadu", "uttar", "madhya",
    "jharkhand", "chhattisgarh", "uttarakhand", "himachal", "manipur", "meghalaya",
    "mizoram", "nagaland", "tripura", "sikkim", "ladakh", "puducherry",
}


def clean_html(text: str) -> str:
    """Strip HTML tags, decode HTML entities, and normalize whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = html.unescape(clean)
    return " ".join(clean.split()).strip()


def extract_tokens(text: str) -> Set[str]:
    """Normalize text by removing punctuation, hyphens, and underscores, returning token set."""
    if not text:
        return set()
    cleaned = re.sub(r"[_\-\.,:;!?\"'()\[\]{}/\\|#@*+~`&]+", " ", text.lower())
    return {t for t in cleaned.split() if len(t) >= 2}


def is_generic_place_name(place_name: str) -> bool:
    """Determine if a place name consists only of generic categories and qualifiers.

    E.g., 'Wax World Museum' consists of qualifier 'wax' and stopwords 'world' and 'museum'.
    'Police Shahid Smarak' consists of qualifier 'police', 'shahid' and category 'smarak'.
    'Archiepiscopal Palace' consists of qualifier 'archiepiscopal' and category 'palace'.
    Distinctive names like 'Aguada Fort' have distinctive proper noun 'aguada'.
    """
    tokens = extract_tokens(place_name)
    meaningful = {
        t for t in tokens
        if t not in GENERIC_STOP_WORDS and t not in LOCATION_WORDS
    }
    if not meaningful:
        return True
    return meaningful.issubset(COMMON_QUALIFIERS)


def extract_conflicting_location_tokens(
    candidate_title: str,
    place_name: str,
    target_location_tokens: Set[str],
) -> Set[str]:
    """Detect if the candidate title explicitly identifies a different city or region.

    Extracts structural location segments (after hyphens, commas, inside parentheses,
    or after prepositions 'in/at/near/of/de') and verifies whether any non-stopword tokens
    conflict with target location tokens and place name tokens.
    """
    if not target_location_tokens:
        return set()

    clean_title = re.sub(r"^file:\s*", "", candidate_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\.[a-zA-Z0-9]+$", "", clean_title)

    title_tokens = extract_tokens(clean_title)
    # If the title explicitly contains any target location token (e.g. 'goa'),
    # it is verified to be within the target location; no conflict.
    if target_location_tokens.intersection(title_tokens):
        return set()

    place_tokens = extract_tokens(place_name)
    segments_to_check = []

    # 1. Hyphen / dash separated segments (e.g. "Wax Museum - Mysore", "Aguada Fort - Lisbon")
    dash_parts = re.split(r"\s*[-–—]\s*", clean_title)
    if len(dash_parts) >= 2:
        meaningful_place = {
            t for t in place_tokens
            if t not in GENERIC_STOP_WORDS and t not in LOCATION_WORDS
        }
        for part in dash_parts:
            part_tokens = extract_tokens(part)
            if not part_tokens.intersection(meaningful_place):
                segments_to_check.append(part)

    # 2. Comma separated suffix (e.g. "Wax Museum, Mysore")
    comma_match = re.search(r",\s*([^,]+)$", clean_title)
    if comma_match:
        segments_to_check.append(comma_match.group(1))

    # 3. Parentheses (e.g. "Wax Museum (Mysore)")
    paren_matches = re.findall(r"\(([^)]+)\)", clean_title)
    for m in paren_matches:
        segments_to_check.append(m)

    # 4. Prepositional phrases: e.g. "of Trujillo", "in Mysore", "near Mumbai", "de Trujillo"
    pattern = re.compile(
        r"\b(of|in|at|near|around|from|de|del|di|da)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(clean_title):
        prep = m.group(1).lower()
        target = m.group(2)
        # Check preceding word before the preposition
        start_idx = m.start()
        prefix = clean_title[:start_idx].strip()
        prev_word = prefix.split()[-1].lower() if prefix.split() else ""
        prev_word = re.sub(r"[^\w]", "", prev_word)

        if prep == "of" and prev_word in MEDIA_PREFIX_WORDS:
            # e.g. "view of ...", "photo of ..." describes media subject, not location
            continue

        segments_to_check.append(target)

    conflicting_tokens: Set[str] = set()
    for seg in segments_to_check:
        seg_tokens = extract_tokens(seg)
        candidates = {
            t for t in seg_tokens
            if t not in GENERIC_STOP_WORDS
            and t not in LOCATION_WORDS
            and t not in PHOTO_DESCRIPTIVE_WORDS
            and t not in FILE_PREFIX_EXTENSIONS
            and not t.isdigit()
            and len(t) > 2
            and t not in place_tokens
            and t not in target_location_tokens
        }
        conflicting_tokens.update(candidates)

    # 5. Recognizable regional / state references (e.g. "Mahagujarat movement" in Ahmedabad vs Jaipur)
    for token in title_tokens:
        if token in place_tokens or token in target_location_tokens:
            continue
        for reg in MAJOR_REGIONS:
            if reg in token and reg not in target_location_tokens and reg not in place_tokens:
                conflicting_tokens.add(token)
                break

    return conflicting_tokens


def is_title_relevant(
    candidate_title: str,
    place_name: str,
    location_tokens: Optional[Set[str]] = None,
) -> bool:
    """Determine whether a Wikimedia file title meaningfully relates to the place name.

    1. Normalizes and extracts alphanumeric tokens from both strings.
    2. Filters generic stop words from the query.
    3. Requires meaningful keyword overlap between query and candidate title.
    4. Prevents accepting candidates that only match generic location words.
    5. Rejects candidates explicitly identifying a conflicting city/region.
    6. Requires geographical confirmation for generic place names (e.g. 'Wax World Museum', 'Archiepiscopal Palace').
    7. Allows distinctive proper names (e.g. 'Aguada Fort') even when city is absent, provided no conflict exists.
    """
    query_tokens = extract_tokens(place_name)
    title_tokens = extract_tokens(candidate_title)

    # Remove file metadata tokens ("file", "jpg", etc.) from title
    title_tokens = {t for t in title_tokens if t not in FILE_PREFIX_EXTENSIONS}

    # Extract meaningful tokens excluding generic stopwords
    meaningful_query = {t for t in query_tokens if t not in GENERIC_STOP_WORDS}
    if not meaningful_query and query_tokens:
        meaningful_query = {
            t for t in query_tokens if len(t) > 2 and t not in {"the", "and", "for", "with"}
        }

    overlap = meaningful_query.intersection(title_tokens)
    if not overlap:
        return False

    # Avoid accepting candidates based solely on generic location words (e.g. matching only "goa")
    distinctive_query = meaningful_query - LOCATION_WORDS
    if distinctive_query and not (overlap - LOCATION_WORDS):
        return False

    # Combine location tokens from place_name and explicit parameters
    target_locs: Set[str] = set(location_tokens or set())
    target_locs.update(query_tokens.intersection(LOCATION_WORDS))

    # Reject candidates with explicit location conflicts
    if target_locs:
        conflicts = extract_conflicting_location_tokens(candidate_title, place_name, target_locs)
        if conflicts:
            return False

    # Generic place names require geographical confirmation in the candidate title
    if target_locs and is_generic_place_name(place_name):
        if not target_locs.intersection(title_tokens):
            return False

    # Distinctive place names: ensure distinctive tokens are matched (never match only a generic qualifier)
    if not is_generic_place_name(place_name):
        distinctive_name_tokens = meaningful_query - LOCATION_WORDS - COMMON_QUALIFIERS
        if distinctive_name_tokens and not (overlap.intersection(distinctive_name_tokens)):
            return False

    return True


class WikimediaService:
    """Service to search Wikimedia Commons for place images and attribution."""

    def __init__(
        self,
        api_url: str = WIKIMEDIA_COMMONS_API_URL,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.api_url = api_url
        self.user_agent = user_agent

    def _query_commons(
        self,
        search_query: str,
        timeout: int = 10,
    ) -> Optional[dict]:
        """Make a single search request to Wikimedia Commons API."""
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": search_query,
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": "5",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime",
        }

        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_data = response.read().decode("utf-8")
                return json.loads(raw_data)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            logger.warning(f"Wikimedia API network issue for '{search_query}': {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error querying Wikimedia for '{search_query}': {exc}")
            return None

    def _extract_valid_candidates(
        self,
        pages: dict,
        place_name: str,
        location_tokens: Optional[Set[str]] = None,
    ) -> List[Dict[str, Optional[str]]]:
        """Iterate through candidate pages in relevance order and extract all valid matches."""
        sorted_pages = sorted(pages.values(), key=lambda p: p.get("index", 999))
        candidates: List[Dict[str, Optional[str]]] = []

        for page in sorted_pages:
            title = page.get("title") or ""
            if not is_title_relevant(title, place_name, location_tokens):
                continue

            imageinfo_list = page.get("imageinfo") or []
            if not imageinfo_list:
                continue

            info = imageinfo_list[0]
            img_url = info.get("url")
            mime = info.get("mime", "").lower()

            if not img_url:
                continue

            # Verify the file is an actual image
            is_valid_image = mime.startswith("image/") or any(
                img_url.lower().endswith(ext) for ext in VALID_IMAGE_EXTENSIONS
            )
            if not is_valid_image:
                continue

            # Extract and format attribution
            extmeta = info.get("extmetadata") or {}
            artist_raw = extmeta.get("Artist", {}).get("value")
            license_raw = extmeta.get("LicenseShortName", {}).get("value")

            artist = clean_html(artist_raw) if artist_raw else None
            license_name = clean_html(license_raw) if license_raw else None

            attribution = None
            if artist and license_name:
                attribution = f"{artist} ({license_name})"
            elif artist:
                attribution = artist
            elif license_name:
                attribution = f"Licensed under {license_name}"

            candidates.append({
                "title": title,
                "image_url": img_url,
                "attribution": attribution,
            })

        return candidates

    def _evaluate_pages(
        self,
        pages: dict,
        place_name: str,
        location_tokens: Optional[Set[str]] = None,
    ) -> Optional[Dict[str, Optional[str]]]:
        """Iterate through candidate pages in relevance order and select the first valid match."""
        candidates = self._extract_valid_candidates(pages, place_name, location_tokens)
        return candidates[0] if candidates else None

    def get_candidates(
        self,
        place_name: str,
        city: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 3,
        timeout: int = 10,
    ) -> List[Dict[str, Optional[str]]]:
        """Search Wikimedia Commons for candidate images of the place with location awareness.

        1. Performs tiered search: searches place_name + city/region first, then falls back to place_name alone.
        2. Applies location conflict detection and geographical relevance filtering.
        3. Returns up to `limit` valid candidate dictionaries with 'title', 'image_url', and 'attribution'.
        """
        if not place_name or not place_name.strip() or limit <= 0:
            return []

        clean_name = place_name.strip()

        # Build location tokens from place_name, city, and region
        location_tokens: Set[str] = set()
        if city and city.strip():
            location_tokens.update(extract_tokens(city.strip()))
        if region and region.strip():
            location_tokens.update(extract_tokens(region.strip()))
        name_tokens = extract_tokens(clean_name)
        location_tokens.update(name_tokens.intersection(LOCATION_WORDS))

        # Build tiered search queries in priority order
        search_queries = []

        # Tier 1: Place name + city/region
        if city and city.strip():
            c = city.strip()
            if c.lower() not in clean_name.lower():
                search_queries.append(f"{clean_name} {c}")

        if region and region.strip():
            r = region.strip()
            if r.lower() not in clean_name.lower() and (not city or r.lower() != city.strip().lower()):
                search_queries.append(f"{clean_name} {r}")

        # Tier 2: Fallback search using place name alone
        if clean_name not in search_queries:
            search_queries.append(clean_name)

        collected_candidates: List[Dict[str, Optional[str]]] = []
        seen_urls: Set[str] = set()

        for query in search_queries:
            data = self._query_commons(query, timeout=timeout)
            if data is None:
                continue

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                continue

            candidates = self._extract_valid_candidates(pages, clean_name, location_tokens)
            for cand in candidates:
                url = cand.get("image_url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    collected_candidates.append(cand)
                    if len(collected_candidates) >= limit:
                        return collected_candidates

            if collected_candidates:
                # Prioritize more specific tiered query matches over less specific fallbacks
                break

        return collected_candidates

    def get_image(
        self,
        place_name: str,
        city: Optional[str] = None,
        region: Optional[str] = None,
        timeout: int = 10,
    ) -> Optional[Dict[str, Optional[str]]]:
        """Search Wikimedia Commons for an image of the specified place with location awareness.

        1. Performs tiered search: searches place_name + city/region first, then falls back to place_name alone.
        2. Applies location conflict detection and geographical relevance filtering.
        3. Returns a dictionary with 'image_url' and 'attribution' if found, else None.
        """
        candidates = self.get_candidates(
            place_name=place_name,
            city=city,
            region=region,
            limit=1,
            timeout=timeout,
        )
        return candidates[0] if candidates else None
