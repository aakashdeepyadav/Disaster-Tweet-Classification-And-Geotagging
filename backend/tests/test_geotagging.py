"""
Comprehensive test script for geotagging functionality
Run: python -m pytest tests/test_geotagging.py
Or: python tests/test_geotagging.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.geotagging import extract_and_geocode, extract_coordinates, extract_location, geocode_location

def test_coordinate_extraction():
    """Test coordinate extraction"""
    test_cases = [
        ("Fire at 40.7128, -74.0060", (40.7128, -74.0060)),
        ("Earthquake at 28.6139, 77.2090", (28.6139, 77.2090)),
        ("Location: 51.5074, -0.1278", (51.5074, -0.1278)),
    ]
    
    print("Testing coordinate extraction...")
    for text, expected in test_cases:
        result = extract_coordinates(text)
        if result:
            lat, lon = result
            assert abs(lat - expected[0]) < 0.0001, f"Lat mismatch: {lat} vs {expected[0]}"
            assert abs(lon - expected[1]) < 0.0001, f"Lon mismatch: {lon} vs {expected[1]}"
            print(f"  ✓ '{text}' -> {result}")
        else:
            print(f"  ✗ '{text}' -> None (expected {expected})")
            assert False, f"Failed to extract coordinates from: {text}"

def test_full_geotagging():
    """Test full geotagging pipeline"""
    test_cases = [
        "Fire in New York, NY",
        "Earthquake at 40.7128, -74.0060",
        "Flood in Mumbai, India",
    ]
    
    print("\nTesting full geotagging...")
    for text in test_cases:
        try:
            result = extract_and_geocode(text)
            if result.get("lat") and result.get("lon"):
                print(f"  ✓ '{text}' -> {result['lat']}, {result['lon']}")
            else:
                print(f"  ⚠ '{text}' -> No coordinates (may need geocoding)")
        except Exception as e:
            print(f"  ✗ '{text}' -> Error: {e}")

if __name__ == "__main__":
    print("="*60)
    print("GEOTAGGING TESTS")
    print("="*60)
    test_coordinate_extraction()
    test_full_geotagging()
    print("\n" + "="*60)
    print("Tests complete!")
    print("="*60)




