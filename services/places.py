"""Google Places API service for finding hotels, vets, and attractions."""

import time
import requests
from typing import List, Optional
from models import Hotel, Veterinarian, Attraction, NationalPark
from services.wikipedia import WikipediaHelper
from utils.distance import haversine_distance, calculate_popularity_score
from config import PET_FRIENDLY_CHAINS


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
            
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                
                # Keep good quality standards - pet-friendly doesn't mean low quality!
                if rating < 3.5 or reviews < 50:
                    continue
                
                if any(chain in name.lower() for chain in PET_FRIENDLY_CHAINS):
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
                    hotel.score = calculate_popularity_score(rating, reviews)
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
                vet.score = calculate_popularity_score(rating, reviews)
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
        
        for i in range(len(route_geometry) - 1):
            coord1 = route_geometry[i]
            coord2 = route_geometry[i + 1]
            
            # Calculate distance (coordinates are [lon, lat] in GeoJSON format)
            segment_dist = haversine_distance(coord1[1], coord1[0], coord2[1], coord2[0], 'meters')
            
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
                                    lon=location.get('longitude', lon),
                                    website=place.get('websiteUri', None)
                                )
                                all_parks.append(park)
                                seen_parks.add(place_id)
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    pass  # Continue on error
                
                last_check_distance = cumulative_distance
        
        # Sort by rating * log(reviews) and return unique parks
        all_parks.sort(key=lambda p: calculate_popularity_score(p.rating, p.user_ratings_total), reverse=True)
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
                    lon=place.get('location', {}).get('longitude', lon),
                    website=place.get('websiteUri', None)
                )
                attractions.append(attraction)
            
            # Sort by rating * log(reviews) and return top N
            attractions.sort(key=lambda a: calculate_popularity_score(a.rating, a.user_ratings_total), reverse=True)
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
                
                # Get Wikipedia info for museums
                wiki_info = WikipediaHelper.search_wikipedia(name)
                
                museum = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='museum',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place.get('location', {}).get('latitude', lat),
                    lon=place.get('location', {}).get('longitude', lon),
                    website=place.get('websiteUri', None),
                    wikipedia_url=wiki_info['url'] if wiki_info else None,
                    wikipedia_summary=wiki_info['summary'] if wiki_info else None
                )
                museums.append(museum)
            
            museums.sort(key=lambda m: calculate_popularity_score(m.rating, m.user_ratings_total), reverse=True)
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
                place_lat = place.get('location', {}).get('latitude', lat)
                place_lon = place.get('location', {}).get('longitude', lon)
                
                if rating < 4.0 or reviews < 50:
                    continue
                
                # VERIFY restaurant is actually within reasonable distance (50km max)
                distance_km = haversine_distance(lat, lon, place_lat, place_lon, unit='km')
                if distance_km > 50:
                    continue
                
                restaurant = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='restaurant',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place_lat,
                    lon=place_lon,
                    website=place.get('websiteUri', None)
                )
                restaurants.append(restaurant)
            
            restaurants.sort(key=lambda r: calculate_popularity_score(r.rating, r.user_ratings_total), reverse=True)
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
                place_lat = place.get('location', {}).get('latitude', lat)
                place_lon = place.get('location', {}).get('longitude', lon)
                
                if rating < 4.0:
                    continue
                
                # VERIFY dog park is actually within reasonable distance (50km max)
                distance_km = haversine_distance(lat, lon, place_lat, place_lon, unit='km')
                if distance_km > 50:
                    continue
                
                dog_park = Attraction(
                    name=name,
                    address=place.get('formattedAddress', ''),
                    location=city_name,
                    type='dog_park',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=place_lat,
                    lon=place_lon,
                    website=place.get('websiteUri', None)
                )
                dog_parks.append(dog_park)
            
            dog_parks.sort(key=lambda d: calculate_popularity_score(d.rating, d.user_ratings_total), reverse=True)
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
        
        for i in range(len(route_geometry) - 1):
            coord1 = route_geometry[i]
            coord2 = route_geometry[i + 1]
            segment_dist = haversine_distance(coord1[1], coord1[0], coord2[1], coord2[0], 'meters')
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
                            distance_to_route = haversine_distance(lat, lon, place_lat, place_lon, 'meters')
                            if distance_to_route > 25000:
                                continue
                            
                            # Look for viewpoint keywords
                            name_lower = name.lower()
                            address_lower = place.get('formattedAddress', '').lower()
                            combined = name_lower + ' ' + address_lower
                            
                            viewpoint_keywords = [
                                'overlook', 'viewpoint', 'scenic', 'vista', 'lookout', 
                                'observation', 'panorama', 'view point', 'viewing area',
                                'summit', 'peak', 'point', 'rim', 'canyon view', 'valley view'
                            ]
                            
                            if any(keyword in combined for keyword in viewpoint_keywords):
                                rating = place.get('rating', 0.0)
                                reviews = place.get('userRatingCount', 0)
                                
                                if rating >= 4.3 and reviews >= 100:
                                    viewpoint = Attraction(
                                        name=name,
                                        address=place.get('formattedAddress', ''),
                                        location=f"~{int(cumulative_distance/1609.34)} mi from start",
                                        type='viewpoint',
                                        rating=rating,
                                        user_ratings_total=reviews,
                                        lat=place_lat,
                                        lon=place_lon,
                                        website=place.get('websiteUri', None)
                                    )
                                    viewpoints.append(viewpoint)
                                    seen_viewpoints.add(place_id)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"    ⚠ Viewpoint search error at mile {int(cumulative_distance/1609.34)}: {e}")
                
                last_check_distance = cumulative_distance
        
        viewpoints.sort(key=lambda v: calculate_popularity_score(v.rating, v.user_ratings_total), reverse=True)
        return viewpoints
    
    def find_national_parks_by_state(self, state_name: str, limit: int = None) -> List[NationalPark]:
        """Find all National Park Service sites in a given state."""
        search_query = f"national forest OR national park OR national historic OR national monument {state_name}"
        
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
            national_parks = []
            
            for place in data.get('places', []):
                name = place.get('displayName', {}).get('text', '')
                name_lower = name.lower()
                address = place.get('formattedAddress', '')
                
                if state_name not in address:
                    continue
                
                if not any(keyword in name_lower for keyword in [
                    'national park', 'national monument', 'national recreation area',
                    'national memorial', 'national historic', 'national historical',
                    'national military park', 'national battlefield', 'national seashore',
                    'national lakeshore', 'national preserve', 'national parkway',
                    'national river', 'national wild', 'national scenic', 'national forest'
                ]):
                    continue
                
                if any(skip in name_lower for skip in ['state park', 'city park', 'county park', 'regional park']):
                    continue
                
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                location_data = place.get('location', {})
                
                wiki_info = WikipediaHelper.search_wikipedia(name)
                
                park = NationalPark(
                    name=name,
                    address=address,
                    state=state_name,
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=location_data.get('latitude', 0),
                    lon=location_data.get('longitude', 0),
                    website=place.get('websiteUri', None),
                    wikipedia_url=wiki_info['url'] if wiki_info else None,
                    wikipedia_summary=wiki_info['summary'] if wiki_info else None
                )
                national_parks.append(park)
            
            national_parks.sort(
                key=lambda p: calculate_popularity_score(p.rating, p.user_ratings_total),
                reverse=True
            )
            
            # Additional search for USDA National Forests
            try:
                forest_query = f"National Forest {state_name}"
                forest_request = {"textQuery": forest_query, "maxResultCount": 10}
                
                forest_response = requests.post(
                    self.TEXT_SEARCH_URL,
                    headers=self.headers,
                    json=forest_request,
                    timeout=10
                )
                
                if forest_response.status_code == 200:
                    forest_data = forest_response.json()
                    
                    for place in forest_data.get('places', []):
                        name = place.get('displayName', {}).get('text', '')
                        address = place.get('formattedAddress', '')
                        
                        if state_name not in address or 'national forest' not in name.lower():
                            continue
                        
                        if any(p.name == name for p in national_parks):
                            continue
                        
                        location = place.get('location', {})
                        rating = place.get('rating', 4.5)
                        reviews = place.get('userRatingCount', 10)
                        
                        wiki_info = WikipediaHelper.search_wikipedia(name)
                        
                        forest = NationalPark(
                            name=name,
                            address=address,
                            state=state_name,
                            rating=rating,
                            user_ratings_total=reviews,
                            lat=location.get('latitude', 0.0),
                            lon=location.get('longitude', 0.0),
                            website=place.get('websiteUri', ''),
                            wikipedia_url=wiki_info.get('url') if wiki_info else None,
                            wikipedia_summary=wiki_info.get('summary') if wiki_info else None
                        )
                        national_parks.append(forest)
                        
            except Exception as forest_error:
                print(f"    ℹ Note: Could not search USDA forests: {forest_error}")
            
            national_parks.sort(
                key=lambda p: calculate_popularity_score(p.rating, p.user_ratings_total),
                reverse=True
            )
            
            if limit:
                return national_parks[:limit]
            return national_parks
            
        except Exception as e:
            print(f"    ⚠ Error searching for national parks in {state_name}: {e}")
            return []
    
    def find_monuments_by_state(self, state_name: str, limit: int = None) -> List[Attraction]:
        """Find monuments and memorials in a given state."""
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
                
                if state_name not in address:
                    continue
                
                if not any(keyword in name_lower for keyword in [
                    'monument', 'memorial', 'statue', 'historic site',
                    'historical marker', 'commemorative'
                ]):
                    continue
                
                if any(skip in name_lower for skip in [
                    'cemetery', 'funeral', 'pet memorial', 'plaque company'
                ]):
                    continue
                
                rating = place.get('rating', 0.0)
                reviews = place.get('userRatingCount', 0)
                location_data = place.get('location', {})
                
                wiki_info = WikipediaHelper.search_wikipedia(name)
                
                monument = Attraction(
                    name=name,
                    address=address,
                    location=state_name,
                    type='monument',
                    rating=rating,
                    user_ratings_total=reviews,
                    lat=location_data.get('latitude', 0),
                    lon=location_data.get('longitude', 0),
                    website=place.get('websiteUri', None),
                    wikipedia_url=wiki_info['url'] if wiki_info else None,
                    wikipedia_summary=wiki_info['summary'] if wiki_info else None
                )
                monuments.append(monument)
            
            monuments.sort(
                key=lambda m: calculate_popularity_score(m.rating, m.user_ratings_total),
                reverse=True
            )
            
            if limit:
                return monuments[:limit]
            return monuments
            
        except Exception as e:
            print(f"    ⚠ Error searching for monuments in {state_name}: {e}")
            return []
