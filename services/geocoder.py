"""Geocoding service using OpenStreetMap Nominatim."""

import requests
from typing import Optional, Tuple
from config import STATE_NAME_TO_ABBREV


class NominatimGeocoder:
    """Geocode city names to coordinates."""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'RoadTripPlanner/2.0 (Personal trip planning)'
        }
    
    def geocode(self, address: str) -> Optional[Tuple[float, float, str]]:
        """
        Geocode an address to coordinates.
        
        Returns:
            (lat, lon, display_name) or None
        """
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                result = data[0]
                return (float(result['lat']), float(result['lon']), result['display_name'])
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Reverse geocode coordinates to city name."""
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 10  # City level
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            address = data.get('address', {})
            
            # Try to get city/town name and state - NEVER use county
            city = (address.get('city') or address.get('town') or 
                   address.get('village') or address.get('hamlet'))
            state = address.get('state')
            
            if city and state:
                # Get state abbreviation if possible
                state_abbrev = self._get_state_abbrev(state)
                return f"{city}, {state_abbrev if state_abbrev else state}"
            elif city:
                return city
            # Don't return county names - skip this location if no actual city found
            return None
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None
    
    def _get_state_abbrev(self, state_name: str) -> Optional[str]:
        """Convert state name to abbreviation."""
        return STATE_NAME_TO_ABBREV.get(state_name.lower())
