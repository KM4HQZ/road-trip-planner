#!/usr/bin/env python3
"""
Dynamic Road Trip Planner
Automatically plan a road trip with hotels, parks, vets, and attractions.

Usage:
    python plan_trip.py "Atlanta, GA" "Chicago, IL" --roundtrip
    python plan_trip.py "Denver, CO" "Seattle, WA"
"""

import os
import sys
import json
import time
import math
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from dotenv import load_dotenv
import folium
from folium import plugins

# Load environment variables
load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')


@dataclass
class Location:
    """Represents a location on the trip."""
    name: str
    lat: float
    lon: float
    type: str  # 'start', 'stop', 'destination', 'waypoint'


@dataclass
class Hotel:
    """Hotel information."""
    name: str
    address: str
    location: str
    rating: float
    user_ratings_total: int
    price_level: Optional[str]
    place_id: str
    lat: float
    lon: float
    phone: Optional[str] = None
    website: Optional[str] = None
    score: float = 0.0


@dataclass
class Veterinarian:
    """24/7 Emergency Veterinarian information."""
    name: str
    address: str
    location: str
    rating: float
    user_ratings_total: int
    place_id: str
    lat: float
    lon: float
    phone: Optional[str] = None
    website: Optional[str] = None
    is_24_hours: bool = False
    score: float = 0.0


@dataclass
class Attraction:
    """Park or attraction information."""
    name: str
    address: str
    location: str
    type: str  # 'park', 'attraction'
    rating: float
    user_ratings_total: int
    lat: float
    lon: float


@dataclass
class NationalPark:
    """Major National Park information."""
    name: str
    address: str
    state: str
    rating: float
    user_ratings_total: int
    lat: float
    lon: float
    website: Optional[str] = None


class OSRMRouter:
    """Calculate routes using OSRM."""
    
    BASE_URL = "http://router.project-osrm.org/route/v1/driving"
    
    def get_route(self, waypoints: List[Tuple[float, float]]) -> Dict:
        """
        Get route through multiple waypoints.
        
        Args:
            waypoints: List of (lat, lon) tuples
            
        Returns:
            Route data including distance, duration, and geometry
        """
        # Convert to lon,lat format for OSRM
        coords_str = ";".join([f"{lon},{lat}" for lat, lon in waypoints])
        url = f"{self.BASE_URL}/{coords_str}"
        
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                return {
                    'distance_m': route['distance'],
                    'duration_s': route['duration'],
                    'geometry': route['geometry'],
                    'legs': route.get('legs', []),
                    'success': True
                }
            else:
                return {'success': False, 'error': 'No route found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_cities_along_route(
        self,
        route_data: Dict,
        geocoder: 'NominatimGeocoder'
    ) -> List[Dict]:
        """
        Find major cities along a route using existing route data and reverse geocoding.
        
        Args:
            route_data: Route data from get_route()
            geocoder: NominatimGeocoder instance for reverse geocoding
            
        Returns:
            List of dicts with 'name', 'lat', 'lon', 'distance_mi' keys
        """
        if not route_data['success']:
            return []
        
        geometry = route_data['geometry']['coordinates']
        
        # Sample points along the route every ~100 miles
        cities_found = []
        seen_cities = set()
        cumulative_distance = 0
        last_check_distance = 0
        check_interval_m = 100 * 1609.34  # Check every 100 miles
        
        for i in range(len(geometry) - 1):
            coord1 = geometry[i]
            coord2 = geometry[i + 1]
            
            segment_dist = self._haversine_distance(
                (coord1[1], coord1[0]),
                (coord2[1], coord2[0])
            ) * 1609.34  # meters
            
            cumulative_distance += segment_dist
            
            # Check for cities at this point if we've traveled enough
            if cumulative_distance - last_check_distance >= check_interval_m:
                lat, lon = coord2[1], coord2[0]
                
                # Use reverse geocoding to find city name
                city_name = geocoder.reverse_geocode(lat, lon)
                
                if city_name and city_name not in seen_cities:
                    distance_mi = cumulative_distance / 1609.34
                    cities_found.append({
                        'name': city_name,
                        'lat': lat,
                        'lon': lon,
                        'distance_mi': distance_mi
                    })
                    seen_cities.add(city_name)
                    time.sleep(1)  # Rate limiting for Nominatim
                
                last_check_distance = cumulative_distance
        
        return cities_found
    
    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in miles."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


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
        states = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
            'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
            'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
            'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
            'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
            'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
            'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
            'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
            'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
            'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
            'wisconsin': 'WI', 'wyoming': 'WY'
        }
        return states.get(state_name.lower())


class GooglePlacesFinder:
    """Find hotels, vets, and attractions using Google Places API."""
    
    NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
    TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.id,places.internationalPhoneNumber,places.websiteUri,places.currentOpeningHours,places.regularOpeningHours'
        }
    
    def find_pet_friendly_hotel(self, city_name: str, lat: float, lon: float) -> Optional[Hotel]:
        """Find the top pet-friendly hotel in a city."""
        request_body = {
            "includedTypes": ["lodging"],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 25000  # Increased to 25km radius for better coverage
                }
            },
            "rankPreference": "POPULARITY",
            "maxResultCount": 20
        }
        
        try:
            response = requests.post(
                self.NEARBY_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            hotels = []
            pet_friendly_chains = [
                'la quinta', 'drury', 'kimpton', 'red roof', 'motel 6',
                'best western', 'residence inn', 'towneplace', 'staybridge',
                'aloft', 'element', 'extended stay', 'candlewood', 'homewood',
                'springhill', 'fairfield', 'comfort inn', 'quality inn',
                'sleep inn', 'econo lodge', 'days inn', 'super 8',
                'knights inn', 'travelodge', 'ramada', 'wyndham',
                'howard johnson', 'microtel', 'baymont', 'hampton', 'hilton',
                'marriott', 'hyatt', 'sheraton', 'westin', 'doubletree',
                'holiday inn', 'courtyard', 'country inn'
            ]
            
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                # Keep good quality standards - pet-friendly doesn't mean low quality!
                if rating < 3.5 or reviews < 50:
                    continue
                
                if any(chain in name.lower() for chain in pet_friendly_chains):
                    hotel = Hotel(
                        name=name,
                        address=place.get('formattedAddress', ''),
                        location=city_name,
                        rating=rating,
                        user_ratings_total=reviews,
                        price_level=place.get('priceLevel', None),
                        place_id=place.get('id', ''),
                        lat=place.get('location', {}).get('latitude', lat),
                        lon=place.get('location', {}).get('longitude', lon),
                        phone=place.get('internationalPhoneNumber', None),
                        website=place.get('websiteUri', None)
                    )
                    hotel.score = rating * math.log10(reviews + 1)
                    hotels.append(hotel)
            
            if hotels:
                hotels.sort(key=lambda h: h.score, reverse=True)
                return hotels[0]
            return None
            
        except Exception as e:
            print(f"  Hotel search error for {city_name}: {e}")
            return None
    
    def find_emergency_vet(self, city_name: str, lat: float, lon: float) -> Optional[Veterinarian]:
        """Find the top-rated 24/7 emergency vet in a city."""
        request_body = {
            "includedTypes": ["veterinary_care"],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 25000  # 25km radius for vets
                }
            },
            "maxResultCount": 20
        }
        
        try:
            response = requests.post(
                self.NEARBY_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            vets = []
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                if rating < 3.0 or reviews < 10:
                    continue
                
                # Check if it's truly 24/7 by examining the schedule
                is_24_hours = False
                opening_hours = place.get('regularOpeningHours', {})
                
                if opening_hours:
                    # Check weekday texts for "Open 24 hours" or similar
                    weekday_texts = opening_hours.get('weekdayDescriptions', [])
                    if weekday_texts and len(weekday_texts) == 7:
                        # ALL 7 days must explicitly say "Open 24 hours"
                        open_24_count = sum(1 for day in weekday_texts if 'open 24 hours' in day.lower())
                        is_24_hours = open_24_count == 7
                    
                    # Also check the periods structure if available
                    if not is_24_hours and 'periods' in opening_hours:
                        periods = opening_hours.get('periods', [])
                        # A true 24/7 place often has a single period with no close time
                        if len(periods) == 1:
                            period = periods[0]
                            # Check if it has open but no close (indicating always open)
                            if 'open' in period and 'close' not in period:
                                is_24_hours = True
                
                # Name check as fallback ONLY if we have no hours data at all
                if not opening_hours:
                    name_lower = name.lower()
                    # Be very strict - only trust explicit 24/7 or 24-hour in name
                    if '24/7' in name_lower or '24-hour emergency' in name_lower or '24 hour emergency' in name_lower:
                        is_24_hours = True
                
                vet = Veterinarian(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    rating=rating,
                    user_ratings_total=reviews,
                    place_id=place.get('id', ''),
                    lat=place.get('location', {}).get('latitude', lat),
                    lon=place.get('location', {}).get('longitude', lon),
                    phone=place.get('internationalPhoneNumber', None),
                    website=place.get('websiteUri', None),
                    is_24_hours=is_24_hours
                )
                vet.score = rating * math.log10(reviews + 1)
                # Boost score for 24-hour vets
                if vet.is_24_hours:
                    vet.score *= 1.5
                
                vets.append(vet)
            
            if vets:
                vets.sort(key=lambda v: v.score, reverse=True)
                return vets[0]
            return None
            
        except Exception as e:
            print(f"  Vet search error for {city_name}: {e}")
            return None
    
    def find_parks_along_route(
        self,
        route_geometry: List[List[float]],
        sample_interval_miles: int = 25
    ) -> List[Attraction]:
        """
        Find ALL parks and attractions along the entire route.
        Uses tighter radius and more frequent sampling along the route.
        
        Args:
            route_geometry: List of [lat, lon] coordinates from route
            sample_interval_miles: How often to check for parks along route (default: 25 miles)
            
        Returns:
            List of Attraction objects
        """
        all_parks = []
        seen_parks = set()
        cumulative_distance = 0
        last_check_distance = 0
        check_interval_m = sample_interval_miles * 1609.34
        
        print(f"  Scanning route for parks (every {sample_interval_miles} miles, 5km radius)...")
        
        # Simple haversine function
        def haversine(lat1, lon1, lat2, lon2):
            import math
            R = 6371000  # Earth's radius in meters
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
            return 2 * R * math.asin(math.sqrt(a))
        
        for i in range(len(route_geometry) - 1):
            coord1 = route_geometry[i]
            coord2 = route_geometry[i + 1]
            
            # Calculate distance (coordinates are [lon, lat] in GeoJSON format)
            segment_dist = haversine(coord1[1], coord1[0], coord2[1], coord2[0])
            
            cumulative_distance += segment_dist
            
            # Check for parks at intervals
            if cumulative_distance - last_check_distance >= check_interval_m:
                lat, lon = coord2[1], coord2[0]
                
                # Find parks near this point - TIGHTER radius for route scanning
                request_body = {
                    "includedTypes": ["park", "national_park", "state_park"],
                    "locationRestriction": {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lon},
                            "radius": 5000  # 5km radius - stay close to route
                        }
                    },
                    "maxResultCount": 10
                }
                
                try:
                    response = requests.post(
                        self.NEARBY_SEARCH_URL,
                        headers=self.headers,
                        json=request_body,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for place in data.get('places', []):
                            name = place.get('displayName', {}).get('text', '')
                            place_id = place.get('id', '')
                            
                            # Skip if we've seen this park
                            if place_id in seen_parks:
                                continue
                            
                            rating = place.get('rating', 0.0)
                            reviews = place.get('userRatingCount', 0)
                            
                            # Only include MAJOR parks along route (stricter criteria)
                            if rating >= 4.5 and reviews >= 500:
                                location = place.get('location', {})
                                
                                park = Attraction(
                                    name=name,
                                    address=place.get('formattedAddress', ''),
                                    location=f"~{int(cumulative_distance/1609.34)} mi from start",
                                    type='park',
                                    rating=rating,
                                    user_ratings_total=reviews,
                                    lat=location.get('latitude', lat),
                                    lon=location.get('longitude', lon)
                                )
                                all_parks.append(park)
                                seen_parks.add(place_id)
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    pass  # Continue on error
                
                last_check_distance = cumulative_distance
        
        # Sort by rating * log(reviews) and return unique parks
        all_parks.sort(key=lambda p: p.rating * math.log10(p.user_ratings_total + 1), reverse=True)
        return all_parks
    
    def find_parks_nearby(self, city_name: str, lat: float, lon: float, limit: int = 3) -> List[Attraction]:
        """Find parks and attractions near a city - larger radius for stop exploration."""
        request_body = {
            "includedTypes": ["park", "national_park", "tourist_attraction"],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 40000  # 40km radius for stop cities
                }
            },
            "maxResultCount": 20
        }
        
        try:
            response = requests.post(
                self.NEARBY_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            attractions = []
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                if rating < 3.5 or reviews < 20:
                    continue
                
                attraction = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='park',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place.get('location', {}).get('latitude', lat),
                    lon=place.get('location', {}).get('longitude', lon)
                )
                attractions.append(attraction)
            
            # Sort by rating * log(reviews) and return top N
            attractions.sort(key=lambda a: a.rating * math.log10(a.user_ratings_total + 1), reverse=True)
            return attractions[:limit]
            
        except Exception as e:
            print(f"  Park search error for {city_name}: {e}")
            return []
    
    def find_museums_in_city(self, city_name: str, lat: float, lon: float, limit: int = 3) -> List[Attraction]:
        """Find museums and cultural attractions in a city."""
        request_body = {
            "includedTypes": ["museum", "art_gallery", "historical_landmark"],
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 40000  # 40km radius
                }
            },
            "maxResultCount": 20
        }
        
        try:
            response = requests.post(
                self.NEARBY_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            museums = []
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                if rating < 4.0 or reviews < 100:
                    continue
                
                museum = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='museum',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place.get('location', {}).get('latitude', lat),
                    lon=place.get('location', {}).get('longitude', lon)
                )
                museums.append(museum)
            
            museums.sort(key=lambda m: m.rating * math.log10(m.user_ratings_total + 1), reverse=True)
            return museums[:limit]
            
        except Exception as e:
            print(f"  Museum search error for {city_name}: {e}")
            return []
    
    def find_dog_friendly_restaurants(self, city_name: str, lat: float, lon: float, limit: int = 5) -> List[Attraction]:
        """Find dog-friendly restaurants with outdoor seating."""
        request_body = {
            "textQuery": f"dog friendly restaurant {city_name}",
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 40000
                }
            },
            "maxResultCount": 20
        }
        
        try:
            response = requests.post(
                self.TEXT_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            restaurants = []
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                if rating < 4.0 or reviews < 50:
                    continue
                
                restaurant = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='restaurant',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place.get('location', {}).get('latitude', lat),
                    lon=place.get('location', {}).get('longitude', lon)
                )
                restaurants.append(restaurant)
            
            restaurants.sort(key=lambda r: r.rating * math.log10(r.user_ratings_total + 1), reverse=True)
            return restaurants[:limit]
            
        except Exception as e:
            print(f"  Restaurant search error for {city_name}: {e}")
            return []
    
    def find_dog_parks_in_city(self, city_name: str, lat: float, lon: float, limit: int = 2) -> List[Attraction]:
        """Find dog parks in a city."""
        request_body = {
            "textQuery": f"dog park {city_name}",
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 40000
                }
            },
            "maxResultCount": 15
        }
        
        try:
            response = requests.post(
                self.TEXT_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            dog_parks = []
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                if rating < 4.0:
                    continue
                
                dog_park = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='dog_park',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place.get('location', {}).get('latitude', lat),
                    lon=place.get('location', {}).get('longitude', lon)
                )
                dog_parks.append(dog_park)
            
            dog_parks.sort(key=lambda d: d.rating * math.log10(d.user_ratings_total + 1), reverse=True)
            return dog_parks[:limit]
            
        except Exception as e:
            print(f"  Dog park search error for {city_name}: {e}")
            return []
    
    def find_scenic_viewpoints_along_route(
        self,
        route_geometry: List[List[float]],
        sample_interval_miles: int = 75
    ) -> List[Attraction]:
        """Find scenic viewpoints and overlooks along the route."""
        viewpoints = []
        seen_viewpoints = set()
        cumulative_distance = 0
        last_check_distance = 0
        check_interval_m = sample_interval_miles * 1609.34
        
        def haversine(lat1, lon1, lat2, lon2):
            import math
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
            return 2 * R * math.asin(math.sqrt(a))
        
        for i in range(len(route_geometry) - 1):
            coord1 = route_geometry[i]
            coord2 = route_geometry[i + 1]
            segment_dist = haversine(coord1[1], coord1[0], coord2[1], coord2[0])
            cumulative_distance += segment_dist
            
            if cumulative_distance - last_check_distance >= check_interval_m:
                lat, lon = coord2[1], coord2[0]
                
                # Use text search with location restriction for viewpoints
                request_body = {
                    "textQuery": "scenic viewpoint OR overlook OR vista OR observation point",
                    "locationBias": {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lon},
                            "radius": 25000  # 25km radius
                        }
                    },
                    "maxResultCount": 5
                }
                
                try:
                    response = requests.post(
                        self.TEXT_SEARCH_URL,
                        headers=self.headers,
                        json=request_body,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for place in data.get('places', []):
                            name = place.get('displayName', {}).get('text', '')
                            place_id = place.get('id', '')
                            location_data = place.get('location', {})
                            place_lat = location_data.get('latitude', 0)
                            place_lon = location_data.get('longitude', 0)
                            
                            if place_id in seen_viewpoints:
                                continue
                            
                            # Verify the viewpoint is actually within 25km of the route point
                            distance_to_route = haversine(lat, lon, place_lat, place_lon)
                            if distance_to_route > 25000:  # Skip if more than 25km away
                                continue
                            
                            # Look for viewpoint keywords - more flexible matching
                            name_lower = name.lower()
                            address_lower = place.get('formattedAddress', '').lower()
                            combined = name_lower + ' ' + address_lower
                            
                            # Broader keyword list
                            viewpoint_keywords = [
                                'overlook', 'viewpoint', 'scenic', 'vista', 'lookout', 
                                'observation', 'panorama', 'view point', 'viewing area',
                                'summit', 'peak', 'point', 'rim', 'canyon view', 'valley view'
                            ]
                            
                            if any(keyword in combined for keyword in viewpoint_keywords):
                                rating = place.get('rating', 0.0)
                                reviews = place.get('userRatingCount', 0)
                                
                                # More relaxed criteria
                                if rating >= 4.3 and reviews >= 100:
                                    location_data = place.get('location', {})
                                    viewpoint = Attraction(
                                        name=name,
                                        address=place.get('formattedAddress', ''),
                                        location=f"~{int(cumulative_distance/1609.34)} mi from start",
                                        type='viewpoint',
                                        rating=rating,
                                        user_ratings_total=reviews,
                                        lat=location_data.get('latitude', lat),
                                        lon=location_data.get('longitude', lon)
                                    )
                                    viewpoints.append(viewpoint)
                                    seen_viewpoints.add(place_id)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    # Show errors for debugging
                    print(f"    ⚠ Viewpoint search error at mile {int(cumulative_distance/1609.34)}: {e}")
                
                last_check_distance = cumulative_distance
        
        viewpoints.sort(key=lambda v: v.rating * math.log10(v.user_ratings_total + 1) if v.user_ratings_total > 0 else v.rating, reverse=True)
        return viewpoints
    
    def find_national_parks_by_state(self, state_name: str, limit: int = None) -> List[NationalPark]:
        """
        Find all National Park Service sites in a given state.
        Includes all NPS site types: parks, monuments, historic sites, etc.
        
        Args:
            state_name: Full state name (e.g., "Colorado", "California")
            limit: Maximum number of parks to return (default None = all)
            
        Returns:
            List of NationalPark objects
        """
        # Search for all types of National Park Service sites
        # Use a broader search to catch all variations
        search_query = f"national forest OR national park OR national historic OR national monument {state_name}"
        
        request_body = {
            "textQuery": search_query,
            "maxResultCount": 20  # Get more to filter down
        }
        
        try:
            response = requests.post(
                self.TEXT_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            national_parks = []
            
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                name_lower = name.lower()
                address = place.get('formattedAddress', '')
                
                # VERIFY the park is actually in this state by checking the address
                if state_name not in address:
                    continue
                
                # Include all National Park Service site types AND National Forests
                if not any(keyword in name_lower for keyword in [
                    'national park',
                    'national monument', 
                    'national recreation area',
                    'national memorial',
                    'national historic',
                    'national historical',
                    'national military park',
                    'national battlefield',
                    'national seashore',
                    'national lakeshore',
                    'national preserve',
                    'national parkway',
                    'national river',
                    'national wild',
                    'national scenic',
                    'national forest'
                ]):
                    continue
                
                # Skip state parks, regional parks, etc.
                if any(skip in name_lower for skip in ['state park', 'city park', 'county park', 'regional park']):
                    continue
                
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                # Accept all national parks regardless of ratings/reviews
                location_data = place.get('location', {})
                
                park = NationalPark(
                    name=name,
                    address=address,
                    state=state_name,
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=location_data.get('latitude', 0),
                    lon=location_data.get('longitude', 0),
                    website=place.get('websiteUri', None)
                )
                national_parks.append(park)
            
            # Sort by popularity (rating * log(reviews))
            national_parks.sort(
                key=lambda p: p.rating * math.log10(p.user_ratings_total + 1),
                reverse=True
            )
            
            if limit:
                return national_parks[:limit]
            return national_parks
            
        except Exception as e:
            print(f"    ⚠ Error searching for national parks in {state_name}: {e}")
            return []
    
    def find_monuments_by_state(self, state_name: str, limit: int = None) -> List[Attraction]:
        """
        Find monuments and memorials in a given state.
        
        Args:
            state_name: Full state name (e.g., "Colorado", "California")
            limit: Maximum number of monuments to return (default None = all)
            
        Returns:
            List of Attraction objects with type='monument'
        """
        # Search for monuments and memorials
        search_query = f"monument OR memorial {state_name}"
        
        request_body = {
            "textQuery": search_query,
            "maxResultCount": 20
        }
        
        try:
            response = requests.post(
                self.TEXT_SEARCH_URL,
                headers=self.headers,
                json=request_body,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            monuments = []
            
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                name_lower = name.lower()
                address = place.get('formattedAddress', '')
                
                # VERIFY the monument is actually in this state
                if state_name not in address:
                    continue
                
                # Look for monument/memorial keywords
                if not any(keyword in name_lower for keyword in [
                    'monument', 'memorial', 'statue', 'historic site',
                    'historical marker', 'commemorative'
                ]):
                    continue
                
                # Skip generic or low-quality results
                if any(skip in name_lower for skip in [
                    'cemetery', 'funeral', 'pet memorial', 'plaque company'
                ]):
                    continue
                
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                # Accept all monuments regardless of ratings/reviews
                location_data = place.get('location', {})
                
                monument = Attraction(
                    name=name,
                    address=address,
                    location=state_name,
                    type='monument',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=location_data.get('latitude', 0),
                    lon=location_data.get('longitude', 0)
                )
                monuments.append(monument)
            
            # Sort by popularity (rating * log(reviews))
            monuments.sort(
                key=lambda m: m.rating * math.log10(m.user_ratings_total + 1),
                reverse=True
            )
            
            if limit:
                return monuments[:limit]
            return monuments
            
        except Exception as e:
            print(f"    ⚠ Error searching for monuments in {state_name}: {e}")
            return []


def create_trip_map(
    route_geometry: List[List[float]],
    stops: List[Dict],
    hotels: Dict[str, Hotel],
    vets: Dict[str, Veterinarian],
    attractions: Dict[str, List[Attraction]],  # Changed to dict with categories
    trip_name: str,
    route_data: Dict = None
) -> folium.Map:
    """Create an interactive map for the trip."""
    
    # Calculate map center
    all_lats = [coord[0] for coord in route_geometry]
    all_lons = [coord[1] for coord in route_geometry]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5,
        tiles='cartodbpositron'
    )
    
    # Add tile layers
    folium.TileLayer('cartodbpositron', name='Road Map (Light)').add_to(m)
    folium.TileLayer('openstreetmap', name='Street Map').add_to(m)
    
    # Create feature groups
    route_group = folium.FeatureGroup(name='Route', show=True)
    hotel_group = folium.FeatureGroup(name='🏨 Hotels', show=True)
    vet_group = folium.FeatureGroup(name='🏥 Emergency Vets', show=True)
    stop_group = folium.FeatureGroup(name='📍 Stop Cities', show=True)
    
    # Add route line
    folium.PolyLine(
        locations=route_geometry,
        color='#2E86AB',
        weight=5,
        opacity=0.8,
        popup='Your Road Trip Route'
    ).add_to(route_group)
    
    # Add white border
    folium.PolyLine(
        locations=route_geometry,
        color='white',
        weight=7,
        opacity=0.6,
        interactive=False
    ).add_to(route_group)
    
    # Add stop markers
    for stop in stops:
        folium.CircleMarker(
            location=[stop['lat'], stop['lon']],
            radius=8,
            popup=f"<b>{stop['name']}</b><br>Stop #{stop.get('stop_number', '?')}",
            tooltip=stop['name'],
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.7
        ).add_to(stop_group)
    
    # Add hotels
    for city_name, hotel in hotels.items():
        popup_html = f"<b>🏨 {hotel.name}</b><br>"
        popup_html += f"<b>⭐ {hotel.rating}/5.0</b> ({hotel.user_ratings_total:,} reviews)<br>"
        popup_html += f"Score: {hotel.score:.2f}<br><br>"
        popup_html += f"📍 {hotel.address}<br>"
        if hotel.phone:
            popup_html += f"📞 {hotel.phone}<br>"
        if hotel.website:
            popup_html += f'<br><a href="{hotel.website}" target="_blank">Website</a>'
        
        folium.Marker(
            location=[hotel.lat, hotel.lon],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{hotel.name} - {hotel.rating}⭐",
            icon=folium.Icon(color='red', icon='bed', prefix='fa')
        ).add_to(hotel_group)
    
    # Add distance/time markers between consecutive stops
    if route_data and len(stops) > 1:
        # Create a distance/time group
        distance_group = folium.FeatureGroup(name='📏 Distances & Times', show=True)
        
        # Use ALL stops in order, excluding the return stop to avoid duplicate markers
        stop_cities = [stop for stop in stops if stop['type'] != 'return']
        
        # Calculate distances between consecutive stops
        for i in range(len(stop_cities) - 1):
            current_stop = stop_cities[i]
            next_stop = stop_cities[i + 1]
            
            import math
            
            def haversine_miles(lat1, lon1, lat2, lon2):
                R = 3959  # Earth's radius in miles
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
                return 2 * R * math.asin(math.sqrt(a))
            
            distance_mi = haversine_miles(current_stop['lat'], current_stop['lon'], 
                                          next_stop['lat'], next_stop['lon'])
            
            # Estimate driving time at 60 mph average
            hours = distance_mi / 60.0
            
            # Calculate midpoint for marker placement
            mid_lat = (current_stop['lat'] + next_stop['lat']) / 2
            mid_lon = (current_stop['lon'] + next_stop['lon']) / 2
            
            # Format time display
            if hours >= 1:
                time_str = f"{int(hours)}h {int((hours % 1) * 60)}m"
            else:
                time_str = f"{int(hours * 60)}m"
            
            # Create distance marker with custom div icon
            distance_html = f"""
            <div style="font-size: 11px; font-weight: bold; background-color: rgba(255, 255, 255, 0.95); 
                        border: 2px solid #2E86AB; border-radius: 4px; padding: 2px 5px;
                        box-shadow: 2px 2px 6px rgba(0,0,0,0.4); white-space: nowrap;
                        text-align: center;">
                {distance_mi:.0f} mi<br>{time_str}
            </div>
            """
            
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(html=distance_html),
                popup=f"<b>{current_stop['name']} → {next_stop['name']}</b><br>{distance_mi:.1f} miles<br>~{time_str} driving"
            ).add_to(distance_group)
        
        distance_group.add_to(m)
    
    # Add vets
    for city_name, vet in vets.items():
        popup_html = f"<b>🏥 {vet.name}</b><br>"
        if vet.is_24_hours:
            popup_html += "<b>⏰ 24/7 Emergency</b><br>"
        popup_html += f"<b>⭐ {vet.rating}/5.0</b> ({vet.user_ratings_total:,} reviews)<br>"
        popup_html += f"📍 {vet.address}<br>"
        if vet.phone:
            popup_html += f"📞 {vet.phone}<br>"
        if vet.website:
            popup_html += f'<br><a href="{vet.website}" target="_blank">Website</a>'
        
        folium.Marker(
            location=[vet.lat, vet.lon],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"🏥 {vet.name} - {vet.rating}⭐",
            icon=folium.Icon(color='darkred', icon='plus', prefix='fa')
        ).add_to(vet_group)
    
    # Add attractions with different icons based on type
    icon_config = {
        'national_park': {'color': 'darkgreen', 'icon': 'flag', 'prefix': 'fa', 'emoji': '🏞️'},
        'monument': {'color': 'gray', 'icon': 'monument', 'prefix': 'fa', 'emoji': '🗿'},
        'park': {'color': 'green', 'icon': 'tree', 'prefix': 'fa', 'emoji': '🌲'},
        'museum': {'color': 'purple', 'icon': 'university', 'prefix': 'fa', 'emoji': '🏛️'},
        'restaurant': {'color': 'orange', 'icon': 'cutlery', 'prefix': 'fa', 'emoji': '🍽️'},
        'dog_park': {'color': 'lightgreen', 'icon': 'paw', 'prefix': 'fa', 'emoji': '🐾'},
        'viewpoint': {'color': 'blue', 'icon': 'camera', 'prefix': 'fa', 'emoji': '📸'}
    }
    
    # Create feature groups for each attraction type
    attraction_groups = {}
    for attraction_type in icon_config.keys():
        attraction_groups[attraction_type] = folium.FeatureGroup(name=f"{icon_config[attraction_type]['emoji']} {attraction_type.replace('_', ' ').title()}s")
    
    # Add all attractions to their respective groups
    for category, attraction_list in attractions.items():
        for attraction in attraction_list:
            # Handle national parks specially (they use NationalPark dataclass)
            if category == 'national_parks':
                config = icon_config['national_park']
                popup_html = f"<b>{config['emoji']} {attraction.name}</b><br>"
                popup_html += f"<b>⭐ {attraction.rating}/5.0</b> ({attraction.user_ratings_total:,} reviews)<br>"
                if attraction.address:
                    popup_html += f"📍 {attraction.address}<br>"
                if hasattr(attraction, 'website') and attraction.website:
                    popup_html += f'<br><a href="{attraction.website}" target="_blank">Official Website</a>'
                popup_html += f"<br><i>{attraction.state}</i>"
                
                folium.Marker(
                    location=[attraction.lat, attraction.lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{attraction.name} - {attraction.rating}⭐",
                    icon=folium.Icon(color=config['color'], icon=config['icon'], prefix=config['prefix'])
                ).add_to(attraction_groups['national_park'])
            else:
                # Regular attractions
                config = icon_config.get(attraction.type, icon_config['park'])
                
                popup_html = f"<b>{config['emoji']} {attraction.name}</b><br>"
                popup_html += f"<b>⭐ {attraction.rating}/5.0</b> ({attraction.user_ratings_total:,} reviews)<br>"
                if attraction.address:
                    popup_html += f"📍 {attraction.address}<br>"
                popup_html += f"<i>{attraction.location}</i>"
                
                group = attraction_groups.get(attraction.type)
                if group:
                    folium.Marker(
                        location=[attraction.lat, attraction.lon],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{attraction.name} - {attraction.rating}⭐",
                        icon=folium.Icon(color=config['color'], icon=config['icon'], prefix=config['prefix'])
                    ).add_to(group)
    
    # Add groups to map
    route_group.add_to(m)
    stop_group.add_to(m)
    hotel_group.add_to(m)
    vet_group.add_to(m)
    
    # Add all attraction groups
    for group in attraction_groups.values():
        group.add_to(m)
    
    # Add controls
    folium.LayerControl(collapsed=False).add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl(position='topleft').add_to(m)
    
    # Add custom "Select All / Deselect All" button
    select_all_script = """
    <script>
    // Wait for map to load
    window.addEventListener('load', function() {
        // Find the layer control
        var layerControl = document.querySelector('.leaflet-control-layers');
        if (layerControl) {
            // Create button container
            var buttonDiv = document.createElement('div');
            buttonDiv.style.padding = '6px 10px';
            buttonDiv.style.backgroundColor = '#fff';
            buttonDiv.style.borderTop = '1px solid #ddd';
            buttonDiv.style.marginTop = '5px';
            
            // Create the button
            var toggleButton = document.createElement('button');
            toggleButton.innerHTML = '☑️ Toggle All';
            toggleButton.style.width = '100%';
            toggleButton.style.padding = '5px';
            toggleButton.style.cursor = 'pointer';
            toggleButton.style.backgroundColor = '#f4f4f4';
            toggleButton.style.border = '1px solid #ccc';
            toggleButton.style.borderRadius = '3px';
            toggleButton.style.fontSize = '12px';
            toggleButton.style.fontWeight = 'bold';
            
            // Add hover effect
            toggleButton.onmouseover = function() {
                this.style.backgroundColor = '#e0e0e0';
            };
            toggleButton.onmouseout = function() {
                this.style.backgroundColor = '#f4f4f4';
            };
            
            // Add click handler
            toggleButton.onclick = function() {
                var overlayInputs = document.querySelectorAll('.leaflet-control-layers-overlays input[type="checkbox"]');
                var allChecked = true;
                
                // Check if all are currently checked
                overlayInputs.forEach(function(input) {
                    if (!input.checked) {
                        allChecked = false;
                    }
                });
                
                // Toggle all to opposite state
                overlayInputs.forEach(function(input) {
                    if (allChecked && input.checked) {
                        input.click();
                    } else if (!allChecked && !input.checked) {
                        input.click();
                    }
                });
            };
            
            buttonDiv.appendChild(toggleButton);
            
            // Insert button into layer control
            var overlaysSection = document.querySelector('.leaflet-control-layers-overlays');
            if (overlaysSection) {
                overlaysSection.parentNode.appendChild(buttonDiv);
            }
        }
    });
    </script>
    """
    m.get_root().html.add_child(folium.Element(select_all_script))
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 18px; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <b>{trip_name}</b><br>
        <span style="font-size: 14px;">Generated: {datetime.now().strftime('%Y-%m-%d')}</span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m


def main():
    parser = argparse.ArgumentParser(
        description='Plan a road trip with automatic hotel, vet, and park recommendations'
    )
    parser.add_argument('origin', help='Starting city (e.g., "Atlanta, GA")')
    parser.add_argument('destination', help='Destination city (e.g., "Chicago, IL")')
    parser.add_argument('--via', action='append', help='Additional cities to visit (can be used multiple times). Example: --via "Nashville, TN" --via "Memphis, TN"')
    parser.add_argument('--roundtrip', action='store_true', help='Return to origin on same route (not recommended - use --via instead for variety)')
    parser.add_argument('--stop-distance', type=int, default=250, 
                       help='Target miles between stops (default: 250)')
    
    args = parser.parse_args()
    
    if args.via and args.roundtrip:
        print("Error: Cannot use both --via and --roundtrip. Use --via for a multi-city route with variety.")
        return 1
    
    if not GOOGLE_PLACES_API_KEY:
        print("Error: GOOGLE_PLACES_API_KEY not found in .env file")
        return 1
    
    print("="*70)
    print("🚗 DYNAMIC ROAD TRIP PLANNER 🗺️")
    print("="*70)
    print()
    
    # Initialize services
    geocoder = NominatimGeocoder()
    router = OSRMRouter()
    places_finder = GooglePlacesFinder(GOOGLE_PLACES_API_KEY)
    
    # Geocode origin and destination
    print(f"📍 Geocoding locations...")
    origin_result = geocoder.geocode(args.origin)
    if not origin_result:
        print(f"Error: Could not find '{args.origin}'")
        return 1
    
    origin_lat, origin_lon, origin_display = origin_result
    print(f"  ✓ Origin: {origin_display}")
    
    time.sleep(1)  # Rate limiting
    
    dest_result = geocoder.geocode(args.destination)
    if not dest_result:
        print(f"Error: Could not find '{args.destination}'")
        return 1
    
    dest_lat, dest_lon, dest_display = dest_result
    print(f"  ✓ Destination: {dest_display}")
    
    # Geocode optional via cities
    via_cities = []
    if args.via:
        for via_city in args.via:
            via_result = geocoder.geocode(via_city)
            if not via_result:
                print(f"Error: Could not find '{via_city}'")
                return 1
            via_lat, via_lon, via_display = via_result
            via_cities.append({
                'name': via_city,
                'lat': via_lat,
                'lon': via_lon,
                'display': via_display
            })
            print(f"  ✓ Via: {via_display}")
    print()
    
    # Calculate route
    print(f"🛣️  Calculating route...")
    waypoints = [(origin_lat, origin_lon), (dest_lat, dest_lon)]
    
    if via_cities:
        # Multi-city route: origin -> destination -> via cities -> origin
        waypoints = [(origin_lat, origin_lon), (dest_lat, dest_lon)]
        for via in via_cities:
            waypoints.append((via['lat'], via['lon']))
        waypoints.append((origin_lat, origin_lon))
    elif args.roundtrip:
        # Same route back
        waypoints.append((origin_lat, origin_lon))
    
    route_data = router.get_route(waypoints)
    
    if not route_data['success']:
        print(f"Error: Could not calculate route: {route_data.get('error')}")
        return 1
    
    total_distance_mi = route_data['distance_m'] / 1609.34
    total_duration_h = route_data['duration_s'] / 3600
    
    print(f"  ✓ Total distance: {total_distance_mi:.1f} miles")
    print(f"  ✓ Estimated driving time: {int(total_duration_h)}h {int((total_duration_h % 1) * 60)}m")
    if via_cities:
        route_str = f"{args.origin} → {args.destination}"
        for via in via_cities:
            route_str += f" → {via['name']}"
        route_str += f" → {args.origin}"
        print(f"  ✓ Route: {route_str}")
    elif args.roundtrip:
        print(f"  ✓ Route: {args.origin} → {args.destination} → {args.origin} (same way back)")
    print()
    
    # Find all cities along the route
    print(f"📍 Finding cities along route...")
    all_cities = router.find_cities_along_route(route_data, geocoder)
    print(f"✓ Found {len(all_cities)} cities along route")
    if all_cities:
        print(f"   Cities: {', '.join([c['name'] for c in all_cities[:10]])}" + 
              (f" ...and {len(all_cities)-10} more" if len(all_cities) > 10 else ""))
    print()
    
    # Select strategic stop cities based on distance
    print(f"🎯 Selecting strategic stop cities (~{args.stop_distance} miles apart)...")
    stops = []
    
    # Add origin
    start_location = {
        'name': args.origin,
        'lat': origin_lat,
        'lon': origin_lon,
        'type': 'start',
        'stop_number': 0
    }
    stops.append(start_location)
    
    # Select intermediate stops from cities found along route
    if all_cities:
        last_stop_lat, last_stop_lon = origin_lat, origin_lon
        target_distance_m = args.stop_distance * 1609.34  # Convert miles to meters
        stop_num = 1
        
        for city in all_cities:
            # Calculate distance from last stop
            dist = router._haversine_distance(
                (last_stop_lat, last_stop_lon),
                (city['lat'], city['lon'])
            ) * 1609.34  # Convert to meters
            dist_mi = dist / 1609.34
            
            # Add city as stop if it's roughly the target distance from last stop
            if dist >= target_distance_m * 0.8:  # At least 80% of target distance
                stops.append({
                    'name': city['name'],
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'type': 'stop',
                    'stop_number': stop_num
                })
                print(f"  Stop {stop_num}: {city['name']} (~{dist_mi:.0f} mi from last stop)")
                last_stop_lat, last_stop_lon = city['lat'], city['lon']
                stop_num += 1
    
    # Add destination
    stops.append({
        'name': args.destination,
        'lat': dest_lat,
        'lon': dest_lon,
        'type': 'destination',
        'stop_number': len(stops)
    })
    print(f"  Destination: {args.destination}")
    
    # Add via cities and return if multi-city route
    if via_cities:
        for via in via_cities:
            stops.append({
                'name': via['name'],
                'lat': via['lat'],
                'lon': via['lon'],
                'type': 'via',
                'stop_number': len(stops)
            })
            print(f"  Via: {via['name']}")
        
        stops.append({
            'name': f"{args.origin} (return)",
            'lat': origin_lat,
            'lon': origin_lon,
            'type': 'return',
            'stop_number': len(stops)
        })
        print(f"  Return to: {args.origin}")
    elif args.roundtrip:
        stops.append({
            'name': f"{args.origin} (return)",
            'lat': origin_lat,
            'lon': origin_lon,
            'type': 'return',
            'stop_number': len(stops)
        })
        print(f"  Return to: {args.origin}")
    
    print()
    print(f"✓ Selected {len(stops)} strategic stops")
    print()
    
    # Find hotels for each stop
    print(f"🏨 Finding top pet-friendly hotels...")
    hotels = {}
    for stop in stops:
        if stop['type'] in ['start', 'stop', 'destination', 'via']:
            print(f"  Searching {stop['name']}...")
            hotel = places_finder.find_pet_friendly_hotel(
                stop['name'],
                stop['lat'],
                stop['lon']
            )
            if hotel:
                hotels[stop['name']] = hotel
                print(f"    ✓ {hotel.name} ({hotel.rating}⭐, {hotel.user_ratings_total} reviews)")
            else:
                print(f"    ⚠ No hotels found")
            time.sleep(1)
    print()
    
    # Find vets for each stop
    print(f"🏥 Finding 24/7 emergency veterinarians...")
    vets = {}
    for stop in stops:
        if stop['type'] in ['start', 'stop', 'destination', 'via']:
            print(f"  Searching {stop['name']}...")
            vet = places_finder.find_emergency_vet(
                stop['name'],
                stop['lat'],
                stop['lon']
            )
            if vet:
                vets[stop['name']] = vet
                hours_text = "24/7" if vet.is_24_hours else "Regular hours"
                print(f"    ✓ {vet.name} ({vet.rating}⭐, {hours_text})")
            else:
                print(f"    ⚠ No vets found")
            time.sleep(1)
    print()
    
    # Find all attractions along route and at stop cities
    print(f"🎯 Finding attractions and points of interest...")
    route_geometry = route_data['geometry']['coordinates']
    
    all_attractions = {
        'parks': [],
        'museums': [],
        'restaurants': [],
        'dog_parks': [],
        'viewpoints': [],
        'national_parks': [],
        'monuments': []
    }
    
    # 0. Find national parks in each state we pass through
    print(f"  🏞️ Finding major national parks by state...")
    states_visited = set()
    for city in all_cities:
        # Extract state from city name (format: "City, ST")
        if ', ' in city['name']:
            state_abbrev = city['name'].split(', ')[-1]
            states_visited.add(state_abbrev)
    
    # Convert state abbreviations to full names
    state_abbrev_to_name = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    
    for state_abbrev in sorted(states_visited):
        state_name = state_abbrev_to_name.get(state_abbrev, state_abbrev)
        print(f"    Searching {state_name}...")
        national_parks = places_finder.find_national_parks_by_state(state_name)  # No limit - get all
        all_attractions['national_parks'].extend(national_parks)
        
        # Also find monuments in this state
        monuments = places_finder.find_monuments_by_state(state_name)  # No limit - get all
        all_attractions['monuments'].extend(monuments)
        time.sleep(1)
    
    # 1. Major parks along the route (tighter criteria)
    print(f"  🌲 Scanning for major parks along route...")
    route_parks = places_finder.find_parks_along_route(route_geometry)
    all_attractions['parks'].extend(route_parks)
    
    # 2. Scenic viewpoints along the route
    print(f"  📸 Scanning for scenic viewpoints...")
    viewpoints = places_finder.find_scenic_viewpoints_along_route(route_geometry, sample_interval_miles=75)
    all_attractions['viewpoints'].extend(viewpoints)
    
    # 3. Attractions at stop cities
    print(f"  Searching near stop cities...")
    for stop in stops:
        if stop['type'] in ['start', 'stop', 'destination', 'via']:
            print(f"    {stop['name']}...")
            
            # Parks at cities
            parks = places_finder.find_parks_nearby(stop['name'], stop['lat'], stop['lon'], limit=3)
            all_attractions['parks'].extend(parks)
            
            # Museums
            museums = places_finder.find_museums_in_city(stop['name'], stop['lat'], stop['lon'], limit=3)
            all_attractions['museums'].extend(museums)
            
            # Dog-friendly restaurants
            restaurants = places_finder.find_dog_friendly_restaurants(stop['name'], stop['lat'], stop['lon'], limit=5)
            all_attractions['restaurants'].extend(restaurants)
            
            # Dog parks
            dog_parks = places_finder.find_dog_parks_in_city(stop['name'], stop['lat'], stop['lon'], limit=2)
            all_attractions['dog_parks'].extend(dog_parks)
            
            time.sleep(1)
    
    # Deduplicate attractions by name within each category
    for category in all_attractions:
        seen_names = set()
        unique_attractions = []
        for attraction in all_attractions[category]:
            if attraction.name not in seen_names:
                unique_attractions.append(attraction)
                seen_names.add(attraction.name)
        # Re-sort by score
        unique_attractions.sort(key=lambda a: a.rating * math.log10(a.user_ratings_total + 1) if a.user_ratings_total > 0 else a.rating, reverse=True)
        all_attractions[category] = unique_attractions
    
    # Print summary
    total_attractions = sum(len(v) for v in all_attractions.values())
    print(f"\n✓ Found {total_attractions} total attractions:")
    print(f"   🏞️ National Parks: {len(all_attractions['national_parks'])}")
    print(f"   🗿 Monuments: {len(all_attractions['monuments'])}")
    print(f"   🌲 Parks: {len(all_attractions['parks'])}")
    print(f"   🏛️ Museums: {len(all_attractions['museums'])}")
    print(f"   🍽️ Restaurants: {len(all_attractions['restaurants'])}")
    print(f"   🐾 Dog Parks: {len(all_attractions['dog_parks'])}")
    print(f"   📸 Viewpoints: {len(all_attractions['viewpoints'])}")
    print()
    
    # Create map
    print(f"🗺️  Generating interactive map...")
    map_route_geometry = [[coord[1], coord[0]] for coord in route_data['geometry']['coordinates']]
    
    trip_name = f"Road Trip: {args.origin} → {args.destination}"
    if via_cities:
        for via in via_cities:
            trip_name += f" → {via['name']}"
        trip_name += f" → {args.origin}"
    elif args.roundtrip:
        trip_name += f" → {args.origin}"
    
    trip_map = create_trip_map(
        map_route_geometry,
        stops,
        hotels,
        vets,
        all_attractions,
        trip_name,
        route_data
    )
    
    # Create output directory
    output_dir = Path("trip routes")
    output_dir.mkdir(exist_ok=True)
    
    # Save map
    if via_cities:
        via_names = '_'.join([via['name'].replace(', ', '_').replace(' ', '_') for via in via_cities])
        output_file = f"trip_{args.origin.replace(', ', '_')}_{args.destination.replace(', ', '_')}_via_{via_names}.html"
    else:
        output_file = f"trip_{args.origin.replace(', ', '_')}_{args.destination.replace(', ', '_')}.html"
    output_file = output_file.replace(' ', '_')
    output_path = output_dir / output_file
    trip_map.save(str(output_path))
    print(f"  ✓ Map saved: {output_path}")
    print()
    
    # Save data
    # Flatten all attractions for JSON
    all_attractions_list = []
    for category, attraction_list in all_attractions.items():
        all_attractions_list.extend([asdict(a) for a in attraction_list])
    
    trip_data = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'origin': args.origin,
        'destination': args.destination,
        'via_cities': [via['name'] for via in via_cities] if via_cities else None,
        'roundtrip': args.roundtrip,
        'total_distance_miles': round(total_distance_mi, 1),
        'total_duration_hours': round(total_duration_h, 1),
        'stops': stops,
        'hotels': {city: asdict(hotel) for city, hotel in hotels.items()},
        'vets': {city: asdict(vet) for city, vet in vets.items()},
        'attractions': {
            'national_parks': [asdict(a) for a in all_attractions['national_parks']],
            'monuments': [asdict(a) for a in all_attractions['monuments']],
            'parks': [asdict(a) for a in all_attractions['parks']],
            'museums': [asdict(a) for a in all_attractions['museums']],
            'restaurants': [asdict(a) for a in all_attractions['restaurants']],
            'dog_parks': [asdict(a) for a in all_attractions['dog_parks']],
            'viewpoints': [asdict(a) for a in all_attractions['viewpoints']]
        }
    }
    
    data_file = str(output_path).replace('.html', '_data.json')
    with open(data_file, 'w') as f:
        json.dump(trip_data, f, indent=2)
    print(f"  ✓ Trip data saved: {data_file}")
    
    # Generate summary
    summary_file = str(output_path).replace('.html', '_summary.md')
    with open(summary_file, 'w') as f:
        f.write(f"# {trip_name}\n\n")
        f.write(f"*Generated: {trip_data['generated']}*\n\n")
        f.write(f"## Trip Overview\n\n")
        f.write(f"- **Distance**: {total_distance_mi:.1f} miles\n")
        f.write(f"- **Estimated Driving Time**: {int(total_duration_h)}h {int((total_duration_h % 1) * 60)}m\n")
        f.write(f"- **Number of Stops**: {len(stops)}\n\n")
        
        f.write(f"## Stops\n\n")
        for i, stop in enumerate(stops, 1):
            f.write(f"{i}. {stop['name']}\n")
        f.write("\n")
        
        f.write(f"## Hotels ({len(hotels)} found)\n\n")
        for city, hotel in hotels.items():
            f.write(f"### {city}\n\n")
            f.write(f"**{hotel.name}**\n\n")
            f.write(f"- Rating: {hotel.rating}⭐ ({hotel.user_ratings_total:,} reviews)\n")
            f.write(f"- Address: {hotel.address}\n")
            if hotel.phone:
                f.write(f"- Phone: {hotel.phone}\n")
            if hotel.website:
                f.write(f"- Website: {hotel.website}\n")
            f.write("\n")
        
        f.write(f"## Emergency Veterinarians ({len(vets)} found)\n\n")
        for city, vet in vets.items():
            f.write(f"### {city}\n\n")
            f.write(f"**{vet.name}**")
            if vet.is_24_hours:
                f.write(f" ⏰ **24/7**")
            f.write("\n\n")
            f.write(f"- Rating: {vet.rating}⭐ ({vet.user_ratings_total:,} reviews)\n")
            f.write(f"- Address: {vet.address}\n")
            if vet.phone:
                f.write(f"- Phone: {vet.phone}\n")
            if vet.website:
                f.write(f"- Website: {vet.website}\n")
            f.write("\n")
        
        # Write attraction sections
        if all_attractions['national_parks']:
            f.write(f"## 🏞️ Major National Parks ({len(all_attractions['national_parks'])} found)\n\n")
            for park in all_attractions['national_parks']:
                f.write(f"- **{park.name}** ({park.rating}⭐, {park.user_ratings_total:,} reviews) - {park.state}\n")
                if park.website:
                    f.write(f"  - Website: {park.website}\n")
            f.write("\n")
        
        if all_attractions['monuments']:
            f.write(f"## 🗿 Monuments & Memorials ({len(all_attractions['monuments'])} found)\n\n")
            for monument in all_attractions['monuments']:
                f.write(f"- **{monument.name}** ({monument.rating}⭐, {monument.user_ratings_total:,} reviews) - {monument.location}\n")
            f.write("\n")
        
        if all_attractions['parks']:
            f.write(f"## 🌲 Parks ({len(all_attractions['parks'])} found)\n\n")
            for park in all_attractions['parks'][:20]:  # Top 20
                f.write(f"- **{park.name}** ({park.rating}⭐, {park.user_ratings_total:,} reviews) - {park.location}\n")
            f.write("\n")
        
        if all_attractions['museums']:
            f.write(f"## 🏛️ Museums & Cultural Attractions ({len(all_attractions['museums'])} found)\n\n")
            for museum in all_attractions['museums']:
                f.write(f"- **{museum.name}** ({museum.rating}⭐, {museum.user_ratings_total:,} reviews) - {museum.location}\n")
            f.write("\n")
        
        if all_attractions['restaurants']:
            f.write(f"## 🍽️ Dog-Friendly Restaurants ({len(all_attractions['restaurants'])} found)\n\n")
            for restaurant in all_attractions['restaurants']:
                f.write(f"- **{restaurant.name}** ({restaurant.rating}⭐, {restaurant.user_ratings_total:,} reviews) - {restaurant.location}\n")
            f.write("\n")
        
        if all_attractions['dog_parks']:
            f.write(f"## 🐾 Dog Parks ({len(all_attractions['dog_parks'])} found)\n\n")
            for dog_park in all_attractions['dog_parks']:
                f.write(f"- **{dog_park.name}** ({dog_park.rating}⭐, {dog_park.user_ratings_total:,} reviews) - {dog_park.location}\n")
            f.write("\n")
        
        if all_attractions['viewpoints']:
            f.write(f"## 📸 Scenic Viewpoints ({len(all_attractions['viewpoints'])} found)\n\n")
            for viewpoint in all_attractions['viewpoints']:
                f.write(f"- **{viewpoint.name}** ({viewpoint.rating}⭐, {viewpoint.user_ratings_total:,} reviews) - {viewpoint.location}\n")
            f.write("\n")
    
    print(f"  ✓ Summary saved: {summary_file}")
    print()
    
    print("="*70)
    print("✅ TRIP PLANNING COMPLETE!")
    print("="*70)
    print()
    print(f"📂 Files generated:")
    print(f"   - {output_path} (interactive map)")
    print(f"   - {data_file} (trip data)")
    print(f"   - {summary_file} (summary report)")
    print()
    print(f"🎉 Open {output_path} in your browser to explore your trip!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
