"""
API Configuration for optional enhancements.
All APIs are optional - the project works without any API keys.
Add your API keys here to enable enhanced features.
"""
import os
from typing import Optional

class APIConfig:
    """Configuration for external APIs"""
    
    # Map Services (Optional - for better map tiles)
    # Currently using OpenStreetMap (free, no key needed)
    MAPBOX_ACCESS_TOKEN: Optional[str] = os.getenv("MAPBOX_ACCESS_TOKEN", None)
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY", None)
    
    # Geocoding Services (Optional - for better geocoding)
    # Currently using Nominatim/OpenStreetMap (free, but rate-limited)
    GOOGLE_GEOCODING_API_KEY: Optional[str] = os.getenv("GOOGLE_GEOCODING_API_KEY", None)
    MAPBOX_GEOCODING_TOKEN: Optional[str] = os.getenv("MAPBOX_GEOCODING_TOKEN", None)
    
    # Weather API (Optional - for weather context in disaster analysis)
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY", None)
    
    # Twitter API (Optional - for real-time tweet fetching)
    TWITTER_BEARER_TOKEN: Optional[str] = os.getenv("TWITTER_BEARER_TOKEN", None)
    
    @classmethod
    def get_map_provider(cls) -> str:
        """Get the map provider to use"""
        if cls.MAPBOX_ACCESS_TOKEN:
            return "mapbox"
        elif cls.GOOGLE_MAPS_API_KEY:
            return "google"
        else:
            return "openstreetmap"  # Default, free
    
    @classmethod
    def get_geocoding_provider(cls) -> str:
        """Get the geocoding provider to use"""
        if cls.GOOGLE_GEOCODING_API_KEY:
            return "google"
        elif cls.MAPBOX_GEOCODING_TOKEN:
            return "mapbox"
        else:
            return "nominatim"  # Default, free
    
    @classmethod
    def has_weather_api(cls) -> bool:
        """Check if weather API is available"""
        return cls.OPENWEATHER_API_KEY is not None
    
    @classmethod
    def has_twitter_api(cls) -> bool:
        """Check if Twitter API is available"""
        return cls.TWITTER_BEARER_TOKEN is not None
    
    @classmethod
    def print_status(cls):
        """Print API configuration status"""
        print("\n" + "="*60)
        print("API CONFIGURATION STATUS")
        print("="*60)
        print(f"Map Provider: {cls.get_map_provider()}")
        print(f"Geocoding Provider: {cls.get_geocoding_provider()}")
        print(f"Weather API: {'✅ Enabled' if cls.has_weather_api() else '❌ Not configured'}")
        print(f"Twitter API: {'✅ Enabled' if cls.has_twitter_api() else '❌ Not configured'}")
        print("="*60)
        print("💡 All features work without API keys!")
        print("   Add API keys to enable enhanced features.")
        print("="*60 + "\n")













