import spacy
import re
from geopy.geocoders import Nominatim
from typing import Optional, Dict, Tuple

# Lazy loading to avoid import-time errors
_nlp = None
geolocator = Nominatim(user_agent="disaster_intel_app")

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
    return _nlp

def extract_coordinates(text: str) -> Optional[Tuple[float, float]]:
    """
    Extract latitude and longitude coordinates from text.
    Supports formats like:
    - "40.7128, -74.0060"
    - "40.7128°N, 74.0060°W"
    - "lat: 40.7128, lon: -74.0060"
    - "40.7128 -74.0060"
    """
    print(f"[GEO] Extracting coordinates from: {text[:100]}")
    
    # Pattern 1: "lat, lon" or "lat,lon" (with optional spaces and negative signs)
    # Matches: "40.7128, -74.0060" or "at 40.7128, -74.0060" or "40.7128,-74.0060"
    pattern1 = r'(-?\d+\.?\d+)\s*[,;]\s*(-?\d+\.?\d+)'
    matches = re.findall(pattern1, text)
    print(f"[GEO] Pattern1 matches: {matches}")
    
    for match in matches:
        try:
            lat = float(match[0])
            lon = float(match[1])
            print(f"[GEO] Parsed as: lat={lat}, lon={lon}")
            # Validate ranges - this is the main check
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                # Additional validation: coordinates are usually not both very small (like 0.1, 0.2)
                # But allow if at least one is significant (> 1) or both are reasonable (> 0.01)
                if (abs(lat) > 1 or abs(lon) > 1) or (abs(lat) > 0.01 and abs(lon) > 0.01):
                    print(f"[GEO] Valid coordinates found: {lat}, {lon}")
                    return (lat, lon)
                else:
                    print(f"[GEO] WARNING: Coordinates too small, might be false positive: {lat}, {lon}")
        except ValueError as e:
            print(f"[GEO] Error parsing match {match}: {e}")
            continue
    
    # Pattern 2: "lat: X, lon: Y" or "latitude: X, longitude: Y"
    pattern2 = r'(?:lat|latitude)[:\s]+(-?\d+\.?\d*)[,\s]+(?:lon|lng|longitude)[:\s]+(-?\d+\.?\d*)'
    matches = re.findall(pattern2, text, re.IGNORECASE)
    
    for match in matches:
        try:
            lat = float(match[0])
            lon = float(match[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            continue
    
    # Pattern 3: Space-separated coordinates "40.7128 -74.0060" (without comma)
    pattern3 = r'(-?\d+\.?\d+)\s+(-?\d+\.?\d+)'
    matches = re.findall(pattern3, text)
    
    for match in matches:
        try:
            lat = float(match[0])
            lon = float(match[1])
            # Validate ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                # Additional validation: coordinates are usually not both very small
                if (abs(lat) > 1 or abs(lon) > 1) or (abs(lat) > 0.01 and abs(lon) > 0.01):
                    print(f"[GEO] Valid coordinates found (space-separated): {lat}, {lon}")
                    return (lat, lon)
        except ValueError:
            continue
    
    # Pattern 4: Degrees format "40.7128°N, 74.0060°W"
    pattern4 = r'(-?\d+\.?\d*)°?\s*([NS]?)[,\s]+(-?\d+\.?\d*)°?\s*([EW]?)'
    matches = re.findall(pattern4, text, re.IGNORECASE)
    
    for match in matches:
        try:
            lat = float(match[0])
            lon = float(match[2])
            # Apply direction
            if match[1].upper() == 'S':
                lat = -lat
            if match[3].upper() == 'W':
                lon = -lon
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            continue
    
    return None

def extract_location(text: str):
    """Extract location name using spaCy NER and regex patterns"""
    try:
        # First, try simple pattern-based extraction (works without spaCy)
        # Pattern: "in Location" or "at Location" or "Location" (capitalized words)
        # Common patterns: "in New York", "at California", "New York", etc.
        location_patterns = [
            r'\b(?:in|at|near|from|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',  # "in New York", "at California"
            r'\b([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)',  # "New York", "Los Angeles"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                location = matches[0].strip()
                # Filter out common false positives
                false_positives = ['Fire', 'Earthquake', 'Flood', 'Hurricane', 'Tornado', 'Disaster', 
                                 'Emergency', 'Warning', 'Alert', 'Breaking', 'News', 'Update']
                if location not in false_positives and len(location) > 2:
                    print(f"[GEO] Found location via pattern: {location}")
                    # Try spaCy to confirm, but return pattern result if spaCy fails
                    try:
                        nlp = get_nlp()
                        doc = nlp(text)
                        loc_ents = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
                        if loc_ents:
                            location = ", ".join(loc_ents)
                            print(f"[GEO] Confirmed by spaCy: {location}")
                            return location
                    except:
                        # spaCy not available, use pattern result
                        return location
        
        # Try spaCy NER (only if pattern matching didn't work)
        try:
            nlp = get_nlp()
            doc = nlp(text)
            
            # Get location entities from spaCy
            loc_ents = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
        except Exception as spacy_error:
            print(f"[GEO] spaCy not available: {spacy_error}")
            loc_ents = []
        
        # Also try to extract address patterns (City, State ZIP)
        # Pattern 1: "City, StateName" or "City, StateName ZIP" (full state name like "Texas" or "Punjab")
        # Improved pattern: Look for "in City, State" or just "City, State" (not including disaster words)
        address_pattern1 = r'(?:in|at|near|from|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?),\s*([A-Z][a-zA-Z]+)(?:\s+\d{5})?'
        address_matches1 = re.findall(address_pattern1, text)
        
        if not address_matches1:
            # Try without preposition: "City, State"
            address_pattern1b = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?),\s*([A-Z][a-zA-Z]+)(?:\s+\d{5})?'
            address_matches1 = re.findall(address_pattern1b, text)
        
        if address_matches1:
            city, state = address_matches1[0]
            city = city.strip()
            state = state.strip()
            # Filter out common false positives (street types, but allow full state names)
            street_types = ['RD', 'ST', 'AVE', 'BLVD', 'DR', 'CT', 'LN', 'WAY', 'PL', 'ROAD', 'STREET', 'Services', 'Emergency']
            # Filter out disaster-related words from city name
            disaster_words = ['Fire', 'Flood', 'Earthquake', 'Emergency', 'Disaster', 'Massive', 'Breaking', 'Alert']
            
            if (state.upper() not in street_types and 
                len(city) > 2 and len(state) > 2 and
                not any(word in city for word in disaster_words) and
                city not in disaster_words):
                address = f"{city}, {state}"
                print(f"[GEO] Found address pattern (full state): {address}")
                return address
        
        # Pattern 2: "City, StateAbbr" or "City, StateAbbr ZIP" (2-letter state code like "TX")
        address_pattern2 = r'([A-Z][a-zA-Z\s]+?),\s*([A-Z]{2})(?:\s+\d{5})?'
        address_matches2 = re.findall(address_pattern2, text)
        
        if address_matches2:
            city, state = address_matches2[0]
            city = city.strip()
            state = state.strip()
            # Filter out common false positives
            if state not in ['RD', 'ST', 'AVE', 'BLVD', 'DR', 'CT', 'LN', 'WAY', 'PL'] and len(city) > 2:
                address = f"{city}, {state}"
                print(f"[GEO] Found address pattern (state abbrev): {address}")
                return address
        
        # Pattern 3: "City State" (without comma)
        city_state_pattern = r'([A-Z][a-zA-Z\s]+?)\s+([A-Z]{2})(?:\s+\d{5})?'
        city_state_matches = re.findall(city_state_pattern, text)
        if city_state_matches:
            city, state = city_state_matches[0]
            city = city.strip()
            state = state.strip()
            # Filter out common false positives
            if state not in ['RD', 'ST', 'AVE', 'BLVD', 'DR', 'CT', 'LN', 'WAY', 'PL'] and len(city) > 2:
                address = f"{city}, {state}"
                print(f"[GEO] Found city-state pattern: {address}")
                return address
        
        if loc_ents:
            # Use combined location phrase if multiple (e.g. "Phagwara, Punjab")
            location = ", ".join(loc_ents)
            print(f"[GEO] Found NER entities: {location}")
            return location
        
        # Try to find state abbreviations (2 uppercase letters)
        state_pattern = r'\b([A-Z]{2})\b'
        states = re.findall(state_pattern, text)
        # Common US state abbreviations
        us_states = {'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'}
        
        for state in states:
            if state in us_states:
                # Find text before state that might be city
                state_index = text.find(state)
                if state_index > 0:
                    # Get last word or two before state
                    before_state = text[:state_index].strip()
                    words = before_state.split()
                    if len(words) >= 1:
                        # Take last 1-2 words as potential city
                        city = " ".join(words[-2:]) if len(words) >= 2 else words[-1]
                        # Clean up city name
                        city = re.sub(r'[^\w\s]', '', city).strip()
                        city = re.sub(r'\d+', '', city).strip()  # Remove numbers
                        if city and len(city) > 2:
                            location = f"{city}, {state}"
                            print(f"[GEO] Extracted from state pattern: {location}")
                            return location
        
        # Final fallback: Try to extract capitalized words that might be locations
        # Look for capitalized words (potential city/state names)
        capitalized_words = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        # Filter out common non-location words
        common_words = {'Fire', 'Earthquake', 'Flood', 'Hurricane', 'Tornado', 'Disaster', 
                       'Emergency', 'Warning', 'Alert', 'Breaking', 'News', 'Update', 'Family',
                       'Needs', 'Rescuing', 'Help', 'Please', 'Call', 'Report', 'Apt', 'Road', 'Rd'}
        potential_locations = [w for w in capitalized_words if w not in common_words and len(w) > 3]
        
        if potential_locations:
            # Take the longest capitalized phrase (likely to be location)
            location = max(potential_locations, key=len)
            print(f"[GEO] Fallback extraction: {location}")
            return location
        
        print(f"[GEO] No location found in text")
        return None
    except Exception as e:
        print(f"[WARNING] Location extraction error: {e}")
        import traceback
        traceback.print_exc()
        # Final fallback: try simple pattern even on error
        try:
            # Pattern: "in Location" or "at Location"
            fallback_match = re.search(r'\b(?:in|at|near|from|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', text)
            if fallback_match:
                location = fallback_match.group(1)
                # Filter out false positives
                false_positives = ['Fire', 'Earthquake', 'Flood', 'Hurricane', 'Tornado']
                if location not in false_positives:
                    print(f"[GEO] Fallback pattern found: {location}")
                    return location
        except:
            pass
        return None


def geocode_location(location_str: str, default_country: Optional[str] = None):
    """Geocode location name to coordinates"""
    if not location_str or not location_str.strip():
        print(f"[GEO] Empty location string provided")
        return None

    location_str = location_str.strip()

    # Try multiple geocoding strategies
    queries_to_try = []
    
    # Strategy 1: Use location as-is
    queries_to_try.append(location_str)
    
    # Strategy 2: Add default country if provided (prioritize this)
    if default_country and default_country.lower() not in location_str.lower():
        queries_to_try.append(f"{location_str}, {default_country}")
    
    # Strategy 3: Add "USA" if it looks like US location (has state abbreviation)
    if re.search(r'\b[A-Z]{2}\b', location_str) and default_country != "USA":
        queries_to_try.append(f"{location_str}, USA")
    
    # Strategy 4: Try with "United States" for US locations
    if re.search(r'\b[A-Z]{2}\b', location_str):
        queries_to_try.append(f"{location_str}, United States")
    
    # Strategy 5: For Indian locations, try variations
    indian_indicators = ['punjab', 'maharashtra', 'gujarat', 'rajasthan', 'tamil nadu', 'karnataka',
                        'west bengal', 'uttar pradesh', 'bihar', 'madhya pradesh', 'andhra pradesh',
                        'odisha', 'assam', 'jharkhand', 'haryana', 'delhi', 'kerala', 'himachal pradesh']
    if any(indicator in location_str.lower() for indicator in indian_indicators):
        if "India" not in location_str:
            queries_to_try.append(f"{location_str}, India")
        queries_to_try.append(f"{location_str}, Punjab, India")  # If Punjab is mentioned
        queries_to_try.append(f"{location_str}, IN")  # ISO country code
    
    # Try each query
    for query in queries_to_try:
        try:
            print(f"[GEO] Trying to geocode: {query}")
            loc = geolocator.geocode(query, timeout=10, exactly_one=True)
            if loc:
                result = {
                    "name": loc.address if hasattr(loc, 'address') else query,
                    "lat": loc.latitude,
                    "lon": loc.longitude,
                }
                print(f"[GEO] Successfully geocoded: {query} -> {loc.latitude}, {loc.longitude}")
                return result
            else:
                print(f"[GEO] No results for: {query}")
        except Exception as e:
            print(f"[WARNING] Geocoding error for '{query}': {e}")
            continue
    
    print(f"[GEO] Could not geocode: {location_str}")
    return None


def extract_and_geocode(text: str) -> Dict:
    """
    Extract location from text - tries coordinates first, then location names.
    Returns dict with location_mention, location, lat, lon
    """
    result = {
        "location_mention": None,
        "location": None,
        "lat": None,
        "lon": None,
        "source": None  # "coordinates" or "geocoded"
    }
    
    # First, try to extract coordinates directly
    coords = extract_coordinates(text)
    if coords:
        lat, lon = coords
        result["lat"] = lat
        result["lon"] = lon
        result["location_mention"] = f"{lat:.4f}, {lon:.4f}"
        result["location"] = f"Coordinates: {lat:.4f}, {lon:.4f}"
        result["source"] = "coordinates"
        print(f"[GEO] Extracted coordinates: {lat}, {lon}")
        return result
    
    # If no coordinates, try to extract location name
    loc_mention = extract_location(text)
    if loc_mention:
        result["location_mention"] = loc_mention
        print(f"[GEO] Extracted location name: {loc_mention}")
        
        # Try geocoding strategies with multiple fallbacks
        geo = None
        
        # Detect if it's likely an Indian location (common Indian states/cities)
        indian_indicators = ['Punjab', 'Maharashtra', 'Gujarat', 'Rajasthan', 'Tamil Nadu', 'Karnataka',
                           'West Bengal', 'Uttar Pradesh', 'Bihar', 'Madhya Pradesh', 'Andhra Pradesh',
                           'Odisha', 'Assam', 'Jharkhand', 'Haryana', 'Delhi', 'Kerala', 'Himachal Pradesh',
                           'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune',
                           'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal',
                           'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra',
                           'Nashik', 'Faridabad', 'Meerut', 'Rajkot', 'Jalandhar', 'Phagwara']
        
        is_indian_location = any(indicator.lower() in loc_mention.lower() for indicator in indian_indicators)
        
        # Strategy 1: If it's an Indian location, try India first
        if is_indian_location:
            print(f"[GEO] Location looks like Indian location, trying India first...")
            geo = geocode_location(loc_mention, default_country="India")
        
        # Strategy 2: If location contains state abbreviation (2 uppercase letters), try USA
        if not geo and re.search(r'\b[A-Z]{2}\b', loc_mention):
            print(f"[GEO] Location looks like US location, trying USA first...")
            geo = geocode_location(loc_mention, default_country="USA")
        
        # Strategy 3: Try without country
        if not geo:
            print(f"[GEO] Trying without country...")
            geo = geocode_location(loc_mention, default_country=None)
        
        # Strategy 4: Try with common countries (prioritize India if it looks Indian)
        if not geo:
            countries = ["India", "USA", "United States"] if is_indian_location else ["USA", "India", "United States"]
            for country in countries:
                print(f"[GEO] Trying with {country}...")
                geo = geocode_location(loc_mention, default_country=country)
                if geo:
                    break
        
        if geo:
            result["location"] = geo.get("name")
            result["lat"] = geo.get("lat")
            result["lon"] = geo.get("lon")
            result["source"] = "geocoded"
            print(f"[GEO] Geocoded successfully: {result}")
            return result
        else:
            print(f"[GEO] Geocoding failed for: {loc_mention}")
            return result
    
    # If nothing found, return empty result
    return result
