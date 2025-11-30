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
from config import STATE_ABBREV_TO_NAME, TripConfig
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
            
            # Create trip configuration from params
            trip_config = TripConfig(
                search_hotels=self.params.get('search_hotels', True),
                pet_friendly_only=self.params.get('pet_friendly_only', True),
                search_vets=self.params.get('search_vets', True),
                search_national_parks=self.params.get('search_national_parks', True),
                search_monuments=self.params.get('search_monuments', True),
                search_parks=self.params.get('search_parks', True),
                search_museums=self.params.get('search_museums', True),
                search_restaurants=self.params.get('search_restaurants', True),
                search_dog_parks=self.params.get('search_dog_parks', True),
                search_viewpoints=self.params.get('search_viewpoints', True),
                search_ev_chargers=self.params.get('search_ev_chargers', True),
                export_gpx=self.params.get('export_gpx', True),
                export_map=self.params.get('export_map', True),
                export_summary=self.params.get('export_summary', True),
                export_data=self.params.get('export_data', True)
            )
            
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
            hotels = {}
            waypoint_hotels = {}
            
            if trip_config.search_hotels:
                hotel_type = "pet-friendly hotels" if trip_config.pet_friendly_only else "hotels"
                self.progress.emit(f'Finding {hotel_type}...')
                
                for i, stop in enumerate(major_stops):
                    self.progress.emit(f'Finding hotel for {stop["name"]}... ({i+1}/{len(major_stops)})')
                    hotel_result = places_finder.find_pet_friendly_hotel(
                        stop['name'], stop['lat'], stop['lon'],
                        pet_friendly_only=trip_config.pet_friendly_only
                    )
                    if hotel_result:
                        hotels[stop['name']] = hotel_result
                    time.sleep(0.5)
                
                for i, waypoint in enumerate(waypoint_cities):
                    self.progress.emit(f'Finding waypoint hotel... ({i+1}/{len(waypoint_cities)})')
                    hotel_result = places_finder.find_pet_friendly_hotel(
                        waypoint['name'], waypoint['lat'], waypoint['lon'],
                        pet_friendly_only=trip_config.pet_friendly_only
                    )
                    if hotel_result:
                        waypoint_hotels[waypoint['name']] = hotel_result
                    time.sleep(0.5)
            
            # Find vets
            vets = {}
            if trip_config.search_vets:
                self.progress.emit('Finding emergency veterinarians...')
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
                'monuments': [],
                'ev_chargers': []
            }
            
            # National parks and monuments by state
            if trip_config.search_national_parks or trip_config.search_monuments:
                self.progress.emit('Finding parks and monuments by state...')
                states_visited = set()
                for city in all_cities:
                    if ',' in city['name']:
                        state = city['name'].split(',')[-1].strip()
                        if len(state) == 2 and state.isupper():
                            states_visited.add(state)
                
                for stop in major_stops:
                    if ',' in stop['name']:
                        state = stop['name'].split(',')[-1].strip()
                        if len(state) == 2 and state.isupper():
                            states_visited.add(state)
                
                for state_abbrev in sorted(states_visited):
                    state_name = STATE_ABBREV_TO_NAME.get(state_abbrev, state_abbrev)
                    self.progress.emit(f'Searching {state_name}...')
                    
                    if trip_config.search_national_parks:
                        parks = places_finder.find_national_parks_by_state(state_name)
                        all_attractions['national_parks'].extend(parks)
                    
                    if trip_config.search_monuments:
                        monuments = places_finder.find_monuments_by_state(state_name)
                        all_attractions['monuments'].extend(monuments)
                    
                    time.sleep(1)
            
            # Parks along route
            if trip_config.search_parks:
                self.progress.emit('Scanning for parks along route...')
                route_parks = places_finder.find_parks_along_route(route_geometry)
                all_attractions['parks'].extend(route_parks)
            
            # Viewpoints
            if trip_config.search_viewpoints:
                self.progress.emit('Finding scenic viewpoints...')
                viewpoints = places_finder.find_scenic_viewpoints_along_route(route_geometry, sample_interval_miles=25)
                all_attractions['viewpoints'].extend(viewpoints)
            
            # EV chargers along route
            if trip_config.search_ev_chargers:
                self.progress.emit('Finding EV charging stations along route...')
                route_chargers = places_finder.find_ev_chargers_along_route(
                    route_geometry,
                    sample_interval_miles=25
                )
                all_attractions['ev_chargers'].extend(route_chargers)
            
            # Attractions at stop cities
            if any([trip_config.search_parks, trip_config.search_museums, trip_config.search_restaurants, trip_config.search_dog_parks, trip_config.search_ev_chargers]):
                for i, stop in enumerate(major_stops):
                    self.progress.emit(f'Finding attractions near {stop["name"]}... ({i+1}/{len(major_stops)})')
                    
                    if trip_config.search_parks:
                        parks = places_finder.find_parks_nearby(stop['name'], stop['lat'], stop['lon'])
                        all_attractions['parks'].extend(parks)
                    
                    if trip_config.search_museums:
                        museums = places_finder.find_museums_in_city(stop['name'], stop['lat'], stop['lon'])
                        all_attractions['museums'].extend(museums)
                    
                    if trip_config.search_restaurants:
                        restaurants = places_finder.find_dog_friendly_restaurants(stop['name'], stop['lat'], stop['lon'])
                        all_attractions['restaurants'].extend(restaurants)
                    
                    if trip_config.search_dog_parks:
                        dog_parks = places_finder.find_dog_parks_in_city(stop['name'], stop['lat'], stop['lon'])
                        all_attractions['dog_parks'].extend(dog_parks)
                    
                    if trip_config.search_ev_chargers:
                        ev_chargers = places_finder.find_ev_chargers_in_city(
                            stop['name'], stop['lat'], stop['lon'],
                            limit=3
                        )
                        all_attractions['ev_chargers'].extend(ev_chargers)
                
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
            
            # Create map if needed
            trip_map = None
            if trip_config.export_map:
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
            else:
                # Still need these for GPX and other exports
                map_route_geometry = [[coord[1], coord[0]] for coord in route_geometry]
                trip_name = f"Road Trip: {self.params['origin']} → {self.params['destination']}"
                if via_cities:
                    for _, _, via_display in via_cities:
                        trip_name += f" → {via_display}"
                if self.params.get('roundtrip'):
                    trip_name += f" → {self.params['origin']}"
            
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
                output_base = f"trip_{self.params['origin'].replace(', ', '_').replace(' ', '_')}_{self.params['destination'].replace(', ', '_').replace(' ', '_')}_via_{via_names}"
            else:
                output_base = f"trip_{self.params['origin'].replace(', ', '_').replace(' ', '_')}_{self.params['destination'].replace(', ', '_').replace(' ', '_')}"
            
            output_files = {}
            
            # Save map if enabled
            if trip_config.export_map:
                output_path = output_dir / (output_base + '.html')
                trip_map.save(str(output_path))
                output_files['map'] = str(output_path)
            
            # Save trip data if enabled
            if trip_config.export_data:
                data_file = output_dir / (output_base + '_data.json')
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
                    'config': {
                        'search_hotels': trip_config.search_hotels,
                        'pet_friendly_only': trip_config.pet_friendly_only,
                        'search_vets': trip_config.search_vets,
                        'search_national_parks': trip_config.search_national_parks,
                        'search_monuments': trip_config.search_monuments,
                        'search_parks': trip_config.search_parks,
                        'search_museums': trip_config.search_museums,
                        'search_restaurants': trip_config.search_restaurants,
                        'search_dog_parks': trip_config.search_dog_parks,
                        'search_viewpoints': trip_config.search_viewpoints,
                        'search_ev_chargers': trip_config.search_ev_chargers
                    },
                    'output_files': output_files
                }
                
                import json
                with open(data_file, 'w') as f:
                    json.dump(trip_data, f, indent=2)
                output_files['data'] = str(data_file)
            else:
                # Still need trip_data for the GUI
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
                    'config': {
                        'search_hotels': trip_config.search_hotels,
                        'pet_friendly_only': trip_config.pet_friendly_only,
                        'search_vets': trip_config.search_vets,
                        'search_national_parks': trip_config.search_national_parks,
                        'search_monuments': trip_config.search_monuments,
                        'search_parks': trip_config.search_parks,
                        'search_museums': trip_config.search_museums,
                        'search_restaurants': trip_config.search_restaurants,
                        'search_dog_parks': trip_config.search_dog_parks,
                        'search_viewpoints': trip_config.search_viewpoints,
                        'search_ev_chargers': trip_config.search_ev_chargers
                    },
                    'output_files': output_files
                }
            
            # Generate GPX if enabled
            if trip_config.export_gpx:
                self.progress.emit('Generating GPX file...')
                gpx_file = output_dir / (output_base + '.gpx')
                create_gpx_file(
                    map_route_geometry,
                    major_stops,
                    waypoint_cities,
                    hotels,
                    waypoint_hotels,
                    vets,
                    all_attractions,
                    trip_name,
                    str(gpx_file)
                )
                output_files['gpx'] = str(gpx_file)
            
            # Generate summary if enabled
            if trip_config.export_summary:
                summary_file = output_dir / (output_base + '_summary.md')
                with open(summary_file, 'w') as f:
                    f.write(f"# {trip_name}\n\n")
                    f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    f.write(f"**Distance**: {total_distance_mi:.1f} miles\n\n")
                    f.write(f"**Driving Time**: {int(total_duration_h)}h {int((total_duration_h % 1) * 60)}m\n\n")
                    f.write(f"**Major Stops**: {len(major_stops)}\n\n")
                    f.write(f"**Hotels Found**: {len(hotels)}\n\n")
                    f.write(f"**Emergency Vets**: {len(vets)}\n\n")
                output_files['summary'] = str(summary_file)
            
            # Update trip data with final output files
            trip_data['output_files'] = output_files
            
            self.progress.emit('Trip planning complete!')
            self.finished.emit(trip_data)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.error.emit(f"{str(e)}\n\nDetails:\n{error_details}")
