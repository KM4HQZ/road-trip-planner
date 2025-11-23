"""Route calculation service using OSRM."""

import time
import requests
from typing import List, Dict, Tuple
from utils.distance import haversine_distance


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
        geocoder
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
        
        # Sample points along the route every ~50 miles (more frequent for better coverage)
        cities_found = []
        seen_cities = set()
        cumulative_distance = 0
        last_check_distance = 0
        check_interval_m = 50 * 1609.34  # Check every 50 miles
        
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
        return haversine_distance(coord1[0], coord1[1], coord2[0], coord2[1], 'miles')
