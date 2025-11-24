"""Background thread for trip planning to keep GUI responsive."""

from PyQt6.QtCore import QThread, pyqtSignal
import sys
import os
from pathlib import Path

# Add parent directory to path to import trip planner modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from services import WikipediaHelper, NominatimGeocoder, OSRMRouter, GooglePlacesFinder
from models import Hotel, Veterinarian, Attraction, NationalPark
from utils import haversine_distance, calculate_popularity_score, create_trip_map, create_gpx_file
from config import STATE_ABBREV_TO_NAME
import time
from datetime import datetime
from dataclasses import asdict


class TripPlannerThread(QThread):
    """Worker thread for trip planning operations."""
    
    progress = pyqtSignal(str)  # Progress message
    finished = pyqtSignal(dict)  # Trip data
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        
    def run(self):
        """Execute trip planning in background."""
        try:
            self.progress.emit('Initializing services...')
            
            # Load API key from the proper location
            from dotenv import load_dotenv
            
            # Check if running as bundled app (PyInstaller sets sys.frozen)
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Running as bundled app - load from Documents/RoadTripPlanner
                env_file = Path.home() / 'Documents' / 'RoadTripPlanner' / '.env'
                if env_file.exists():
                    load_dotenv(env_file)
            else:
                # Running from source - use current directory
                load_dotenv()
            
            api_key = os.getenv('GOOGLE_PLACES_API_KEY')
            
            # Initialize services
            geocoder = NominatimGeocoder()
            router = OSRMRouter()
            places_finder = GooglePlacesFinder(api_key)
            
            # Geocode origin
            self.progress.emit(f"Geocoding origin: {self.params['origin']}...")
            origin_result = geocoder.geocode(self.params['origin'])
            if not origin_result:
                self.error.emit(f"Could not geocode origin: {self.params['origin']}")
                return
                
            origin_lat, origin_lon, origin_display = origin_result
            time.sleep(1)
            
            # Geocode destination
            self.progress.emit(f"Geocoding destination: {self.params['destination']}...")
            dest_result = geocoder.geocode(self.params['destination'])
            if not dest_result:
                self.error.emit(f"Could not geocode destination: {self.params['destination']}")
                return
                
            dest_lat, dest_lon, dest_display = dest_result
            
            # Geocode via cities
            via_cities = []
            for via_city in self.params.get('via_cities', []):
                self.progress.emit(f"Geocoding via city: {via_city}...")
                via_result = geocoder.geocode(via_city)
                if via_result:
                    via_lat, via_lon, via_display = via_result
                    via_cities.append((via_lat, via_lon, via_display))
                time.sleep(1)
            
            # Calculate route
            self.progress.emit('Calculating route...')
            waypoints = [(origin_lat, origin_lon), (dest_lat, dest_lon)]
            
            if via_cities:
                waypoints = [(origin_lat, origin_lon)]
                for via_lat, via_lon, _ in via_cities:
                    waypoints.append((via_lat, via_lon))
                waypoints.append((dest_lat, dest_lon))
                if self.params.get('roundtrip'):
                    waypoints.append((origin_lat, origin_lon))
            elif self.params.get('roundtrip'):
                waypoints.append((origin_lat, origin_lon))
            
            route_data = router.get_route(waypoints)
            
            if not route_data['success']:
                self.error.emit(f"Could not calculate route: {route_data.get('error', 'Unknown error')}")
                return
            
            total_distance_mi = route_data['distance_m'] / 1609.34
            total_duration_h = route_data['duration_s'] / 3600
            
            # Find cities along route
            self.progress.emit('Finding cities along route...')
            all_cities = router.find_cities_along_route(route_data, geocoder)
            
            # Select major stops
            self.progress.emit('Selecting major stop cities...')
            major_stops = []
            
            # Add origin
            city_name_only = self.params['origin'].split(',')[0].strip()
            wikivoyage_url = WikipediaHelper.search_wikivoyage(city_name_only)
            
            start_location = {
                'name': self.params['origin'],
                'lat': origin_lat,
                'lon': origin_lon,
                'type': 'start',
                'stop_number': 0,
                'wikivoyage_url': wikivoyage_url,
                'is_major_stop': True
            }
            major_stops.append(start_location)
            
            # Select intermediate stops from cities
            waypoint_cities = []
            target_miles = self.params.get('target_hours', 8) * 65
            
            if all_cities:
                last_stop_lat, last_stop_lon = origin_lat, origin_lon
                
                for city in all_cities:
                    distance = haversine_distance(
                        last_stop_lat, last_stop_lon,
                        city['lat'], city['lon']
                    )
                    
                    if distance >= target_miles:
                        wikivoyage = WikipediaHelper.search_wikivoyage(city['name'].split(',')[0])
                        major_stops.append({
                            'name': city['name'],
                            'lat': city['lat'],
                            'lon': city['lon'],
                            'type': 'stop',
                            'stop_number': len(major_stops),
                            'wikivoyage_url': wikivoyage,
                            'is_major_stop': True
                        })
                        last_stop_lat, last_stop_lon = city['lat'], city['lon']
                    elif distance >= self.params.get('waypoint_interval', 100):
                        waypoint_cities.append({
                            'name': city['name'],
                            'lat': city['lat'],
                            'lon': city['lon'],
                            'type': 'waypoint',
                            'is_major_stop': False
                        })
            
            # Add destination
            dest_city_name = self.params['destination'].split(',')[0].strip()
            dest_wikivoyage = WikipediaHelper.search_wikivoyage(dest_city_name)
            
            major_stops.append({
                'name': self.params['destination'],
                'lat': dest_lat,
                'lon': dest_lon,
                'type': 'destination',
                'stop_number': len(major_stops),
                'wikivoyage_url': dest_wikivoyage,
                'is_major_stop': True
            })
            
            # Add via cities if specified
            if via_cities:
                for via_lat, via_lon, via_display in via_cities:
                    wikivoyage = WikipediaHelper.search_wikivoyage(via_display.split(',')[0])
                    major_stops.append({
                        'name': via_display,
                        'lat': via_lat,
                        'lon': via_lon,
                        'type': 'via',
                        'stop_number': len(major_stops),
                        'wikivoyage_url': wikivoyage,
                        'is_major_stop': True
                    })
            
            if self.params.get('roundtrip'):
                major_stops.append({
                    'name': self.params['origin'] + ' (return)',
                    'lat': origin_lat,
                    'lon': origin_lon,
                    'type': 'return',
                    'stop_number': len(major_stops),
                    'is_major_stop': True
                })
            
            # Find hotels
            self.progress.emit('Finding pet-friendly hotels...')
            hotels = {}
            waypoint_hotels = {}
            
            for i, stop in enumerate(major_stops):
                self.progress.emit(f'Finding hotel for {stop["name"]}... ({i+1}/{len(major_stops)})')
                hotel_result = places_finder.find_pet_friendly_hotel(stop['name'], stop['lat'], stop['lon'])
                if hotel_result:
                    hotels[stop['name']] = hotel_result
                time.sleep(0.5)
            
            for i, waypoint in enumerate(waypoint_cities):
                self.progress.emit(f'Finding waypoint hotel... ({i+1}/{len(waypoint_cities)})')
                hotel_result = places_finder.find_pet_friendly_hotel(waypoint['name'], waypoint['lat'], waypoint['lon'])
                if hotel_result:
                    waypoint_hotels[waypoint['name']] = hotel_result
                time.sleep(0.5)
            
            # Find vets
            self.progress.emit('Finding emergency veterinarians...')
            vets = {}
            for i, stop in enumerate(major_stops):
                self.progress.emit(f'Finding vet for {stop["name"]}... ({i+1}/{len(major_stops)})')
                vet_result = places_finder.find_emergency_vet(stop['name'], stop['lat'], stop['lon'])
                if vet_result:
                    vets[stop['name']] = vet_result
                time.sleep(0.5)
            
            # Find attractions
            self.progress.emit('Finding attractions...')
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
            
            # National parks by state
            self.progress.emit('Finding national parks...')
            states_visited = set()
            for city in all_cities:
                if ',' in city['name']:
                    state = city['name'].split(',')[-1].strip()
                    states_visited.add(state)
            
            for stop in major_stops:
                if ',' in stop['name']:
                    state = stop['name'].split(',')[-1].strip()
                    states_visited.add(state)
            
            for state_abbrev in sorted(states_visited):
                state_name = STATE_ABBREV_TO_NAME.get(state_abbrev, state_abbrev)
                self.progress.emit(f'Searching for parks in {state_name}...')
                parks = places_finder.find_national_parks_by_state(state_name)
                all_attractions['national_parks'].extend(parks[:5])
                time.sleep(1)
            
            # Parks along route
            self.progress.emit('Scanning for parks along route...')
            route_parks = places_finder.find_parks_along_route(route_geometry)
            all_attractions['parks'].extend(route_parks)
            
            # Viewpoints
            self.progress.emit('Finding scenic viewpoints...')
            viewpoints = places_finder.find_scenic_viewpoints_along_route(route_geometry, sample_interval_miles=25)
            all_attractions['viewpoints'].extend(viewpoints)
            
            # Attractions at stop cities
            for i, stop in enumerate(major_stops):
                self.progress.emit(f'Finding attractions near {stop["name"]}... ({i+1}/{len(major_stops)})')
                
                parks = places_finder.find_parks_nearby(stop['name'], stop['lat'], stop['lon'])
                all_attractions['parks'].extend(parks)
                
                museums = places_finder.find_museums_in_city(stop['name'], stop['lat'], stop['lon'])
                all_attractions['museums'].extend(museums)
                
                restaurants = places_finder.find_dog_friendly_restaurants(stop['name'], stop['lat'], stop['lon'])
                all_attractions['restaurants'].extend(restaurants)
                
                dog_parks = places_finder.find_dog_parks_in_city(stop['name'], stop['lat'], stop['lon'])
                all_attractions['dog_parks'].extend(dog_parks)
                
                time.sleep(0.5)
            
            # Deduplicate attractions
            for category in all_attractions:
                seen = set()
                unique = []
                for attraction in all_attractions[category]:
                    if attraction.name not in seen:
                        seen.add(attraction.name)
                        unique.append(attraction)
                all_attractions[category] = unique
            
            # Create map
            self.progress.emit('Generating map...')
            map_route_geometry = [[coord[1], coord[0]] for coord in route_geometry]
            
            trip_name = f"Road Trip: {self.params['origin']} → {self.params['destination']}"
            if via_cities:
                for _, _, via_display in via_cities:
                    trip_name += f" → {via_display}"
            if self.params.get('roundtrip'):
                trip_name += f" → {self.params['origin']}"
            
            trip_map = create_trip_map(
                map_route_geometry,
                major_stops,
                waypoint_cities,
                hotels,
                waypoint_hotels,
                vets,
                all_attractions,
                trip_name,
                route_data
            )
            
            # Save outputs
            self.progress.emit('Saving files...')
            
            # Check if running as bundled app (PyInstaller sets sys.frozen)
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Running as bundled app - save to Documents/RoadTripPlanner/trip routes
                output_dir = Path.home() / 'Documents' / 'RoadTripPlanner' / 'trip routes'
            else:
                # Running from source - use current directory
                output_dir = Path("trip routes")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if via_cities:
                via_names = '_'.join([v[2].replace(', ', '_').replace(' ', '_') for v in via_cities])
                output_file = f"trip_{self.params['origin'].replace(', ', '_').replace(' ', '_')}_{self.params['destination'].replace(', ', '_').replace(' ', '_')}_via_{via_names}.html"
            else:
                output_file = f"trip_{self.params['origin'].replace(', ', '_').replace(' ', '_')}_{self.params['destination'].replace(', ', '_').replace(' ', '_')}.html"
            
            output_path = output_dir / output_file
            trip_map.save(str(output_path))
            
            # Save trip data
            data_file = str(output_path).replace('.html', '_data.json')
            trip_data = {
                'origin': self.params['origin'],
                'destination': self.params['destination'],
                'via_cities': [v[2] for v in via_cities],
                'roundtrip': self.params.get('roundtrip', False),
                'total_distance_miles': round(total_distance_mi, 1),
                'total_duration_hours': round(total_duration_h, 2),
                'generated_at': datetime.now().isoformat(),
                'major_stops': major_stops,
                'waypoint_cities': waypoint_cities,
                'hotels': {k: asdict(v) for k, v in hotels.items()},
                'waypoint_hotels': {k: asdict(v) for k, v in waypoint_hotels.items()},
                'vets': {k: asdict(v) for k, v in vets.items()},
                'attractions': {
                    cat: [asdict(a) for a in attractions]
                    for cat, attractions in all_attractions.items()
                },
                'output_files': {
                    'map': str(output_path),
                    'data': data_file,
                    'summary': str(output_path).replace('.html', '_summary.md'),
                    'gpx': str(output_path).replace('.html', '.gpx')
                }
            }
            
            import json
            with open(data_file, 'w') as f:
                json.dump(trip_data, f, indent=2)
            
            # Generate GPX
            self.progress.emit('Generating GPX file...')
            gpx_file = str(output_path).replace('.html', '.gpx')
            create_gpx_file(
                map_route_geometry,
                major_stops,
                waypoint_cities,
                hotels,
                waypoint_hotels,
                vets,
                all_attractions,
                trip_name,
                gpx_file
            )
            
            # Generate summary (simplified version)
            summary_file = str(output_path).replace('.html', '_summary.md')
            with open(summary_file, 'w') as f:
                f.write(f"# {trip_name}\n\n")
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(f"**Distance**: {total_distance_mi:.1f} miles\n\n")
                f.write(f"**Driving Time**: {int(total_duration_h)}h {int((total_duration_h % 1) * 60)}m\n\n")
                f.write(f"**Major Stops**: {len(major_stops)}\n\n")
                f.write(f"**Hotels Found**: {len(hotels)}\n\n")
                f.write(f"**Emergency Vets**: {len(vets)}\n\n")
            
            self.progress.emit('Trip planning complete!')
            self.finished.emit(trip_data)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.error.emit(f"{str(e)}\n\nDetails:\n{error_details}")
