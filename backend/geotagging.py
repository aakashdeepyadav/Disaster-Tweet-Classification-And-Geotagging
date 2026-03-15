"""Standalone geotagging helpers for runtime prediction.

This module does not import the `disaster_api` package to avoid circular imports.
It supports:
- coordinate extraction
- lightweight location phrase extraction
- geocoding via geopy (when available)
"""

import re
from typing import Dict, Optional, Tuple

try:
    from geopy.geocoders import ArcGIS, Nominatim

    _geocoders = [
        Nominatim(user_agent="disaster_geotag_runtime_v2"),
        ArcGIS(),
    ]
except Exception:
    _geocoders = []

try:
    import geonamescache

    _gc = geonamescache.GeonamesCache()
    _country_name_to_code = {
        v["name"].lower(): k for k, v in _gc.get_countries().items()
    }
    _city_name_index = {}
    for city in _gc.get_cities().values():
        city_name = city.get("name", "").strip().lower()
        if not city_name:
            continue
        prev = _city_name_index.get(city_name)
        city_pop = int(city.get("population") or 0)
        prev_pop = int(prev.get("population") or 0) if prev else -1
        # Keep the most populous city for ambiguous names.
        if city_pop > prev_pop:
            _city_name_index[city_name] = city
except Exception:
    _gc = None
    _country_name_to_code = {}
    _city_name_index = {}


def _offline_geocode_city(location_str: str, default_country: Optional[str] = None):
    if not _city_name_index:
        return None

    candidates = [part.strip().lower() for part in location_str.split(",") if part.strip()]
    if not candidates:
        candidates = [location_str.strip().lower()]

    country_code = None
    if default_country:
        country_code = _country_name_to_code.get(default_country.strip().lower())

    for token in candidates:
        city = _city_name_index.get(token)
        if not city:
            continue
        if country_code and city.get("countrycode") != country_code:
            continue
        return {
            "name": f"{city.get('name')}, {city.get('countrycode')}",
            "lat": float(city.get("latitude")),
            "lon": float(city.get("longitude")),
        }

    return None


def extract_coordinates(text: str) -> Optional[Tuple[float, float]]:
    pattern = r"(-?\d+\.?\d+)\s*[,;]\s*(-?\d+\.?\d+)"
    matches = re.findall(pattern, text)
    if not matches:
        return None

    try:
        lat = float(matches[0][0])
        lon = float(matches[0][1])
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
    except ValueError:
        return None

    return None


def extract_location(text: str) -> Optional[str]:
    patterns = [
        r"\b(?:in|at|near|from)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
        r"\b([A-Z][a-zA-Z]+,\s*[A-Z][a-zA-Z]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            if len(location) >= 3:
                return location

    return None


def extract_location_candidates(text: str) -> list[str]:
    patterns = [
        r"\b(?:in|at|near|from)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
        r"\b([A-Z][a-zA-Z]+,\s*[A-Z][a-zA-Z]+)",
    ]

    candidates = []
    seen = set()

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            location = match.group(1).strip()
            if len(location) < 3:
                continue
            lowered = location.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            candidates.append(location)

    # City-token fallback for ambiguous phrases like "near Yamuna in Delhi".
    for token in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text):
        lowered = token.lower()
        if lowered in seen:
            continue
        if lowered in _city_name_index:
            seen.add(lowered)
            candidates.append(token)

    return candidates


def infer_country_hint(text: str) -> Optional[str]:
    lowered = text.lower()

    country_keyword_map = {
        "India": [" india", "delhi", "mumbai", "kolkata", "chennai", "bengaluru", "bangalore", "hyderabad", "pune"],
        "Nepal": [" nepal", "kathmandu", "pokhara", "lalitpur", "biratnagar"],
        "Pakistan": [" pakistan", "karachi", "lahore", "islamabad", "peshawar"],
        "Bangladesh": [" bangladesh", "dhaka", "chittagong", "khulna", "rajshahi"],
        "Sri Lanka": [" sri lanka", "colombo", "kandy", "galle", "jaffna"],
        "United States": [" usa", " u.s.", "united states", "new york", "los angeles", "chicago", "houston"],
        "United Kingdom": [" uk", "united kingdom", "london", "manchester", "birmingham", "liverpool"],
    }

    for country, keywords in country_keyword_map.items():
        for keyword in keywords:
            if keyword in lowered:
                return country

    return None


def geocode_location(location_str: str, default_country: Optional[str] = None):
    if not location_str:
        return None

    queries = [location_str]
    if default_country and default_country.lower() not in location_str.lower():
        queries.insert(0, f"{location_str}, {default_country}")

    if _geocoders:
        for query in queries:
            for geocoder in _geocoders:
                try:
                    loc = geocoder.geocode(query, timeout=8)
                    if not loc:
                        continue
                    return {
                        "name": getattr(loc, "address", query),
                        "lat": loc.latitude,
                        "lon": loc.longitude,
                    }
                except Exception:
                    continue

    offline = _offline_geocode_city(location_str, default_country=default_country)
    if offline:
        return offline

    return None


def extract_and_geocode(text: str, default_country: Optional[str] = None) -> Dict:
    result = {
        "location_mention": None,
        "location": None,
        "lat": None,
        "lon": None,
        "source": None,
    }

    coords = extract_coordinates(text)
    if coords:
        lat, lon = coords
        result.update(
            {
                "location_mention": f"{lat:.4f}, {lon:.4f}",
                "location": f"Coordinates: {lat:.4f}, {lon:.4f}",
                "lat": lat,
                "lon": lon,
                "source": "coordinates",
            }
        )
        return result

    mentions = extract_location_candidates(text)
    if not mentions:
        return result

    result["location_mention"] = mentions[0]
    country_hint = default_country or infer_country_hint(text)
    for mention in mentions:
        geocoded = geocode_location(mention, default_country=country_hint)
        if not geocoded:
            continue
        result.update(
            {
                "location_mention": mention,
                "location": geocoded["name"],
                "lat": geocoded["lat"],
                "lon": geocoded["lon"],
                "source": "geocoding",
            }
        )
        break

    return result


__all__ = [
    "extract_coordinates",
    "extract_location",
    "extract_location_candidates",
    "infer_country_hint",
    "geocode_location",
    "extract_and_geocode",
]
