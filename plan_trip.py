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
import argparse
from pathlib import Path
from dataclasses import asdict
from datetime import datetime
from dotenv import load_dotenv

# Import models
from models import Hotel, Veterinarian, Attraction, NationalPark

# Import services
from services import WikipediaHelper, NominatimGeocoder, OSRMRouter, GooglePlacesFinder

# Import utilities
from utils import haversine_distance, calculate_popularity_score, create_trip_map, create_gpx_file

# Import configuration
from config import STATE_ABBREV_TO_NAME, TripConfig

# Load environment variables
load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')


def main():
    parser = argparse.ArgumentParser(
        description='Plan a road trip with automatic hotel, vet, and park recommendations'
    )
    parser.add_argument('origin', help='Starting city (e.g., "Atlanta, GA")')
    parser.add_argument('destination', help='Destination city (e.g., "Chicago, IL")')
    parser.add_argument('--via', action='append', help='Additional cities to visit (can be used multiple times). Example: --via "Nashville, TN" --via "Memphis, TN"')
    parser.add_argument('--roundtrip', action='store_true', help='Return to origin on same route (not recommended - use --via instead for variety)')
    parser.add_argument('--target-hours', type=int, default=8, 
                       help='Target driving hours between major stops (default: 8)')
    parser.add_argument('--waypoint-interval', type=int, default=100,
                       help='Miles between waypoint cities for hotel options (default: 100)')
    
    # Search toggles
    search_group = parser.add_argument_group('search options', 'Control what to search for')
    search_group.add_argument('--no-hotels', action='store_true', help='Skip hotel search')
    search_group.add_argument('--all-hotels', action='store_true', help='Search all hotels (not just pet-friendly)')
    search_group.add_argument('--no-vets', action='store_true', help='Skip emergency vet search')
    search_group.add_argument('--no-national-parks', action='store_true', help='Skip national parks')
    search_group.add_argument('--no-monuments', action='store_true', help='Skip monuments and memorials')
    search_group.add_argument('--no-parks', action='store_true', help='Skip parks')
    search_group.add_argument('--no-museums', action='store_true', help='Skip museums')
    search_group.add_argument('--no-restaurants', action='store_true', help='Skip dog-friendly restaurants')
    search_group.add_argument('--no-dog-parks', action='store_true', help='Skip dog parks')
    search_group.add_argument('--no-viewpoints', action='store_true', help='Skip scenic viewpoints')
    search_group.add_argument('--no-ev-chargers', action='store_true', help='Skip EV charging station search')
    
    # Export options
    
    # Export toggles
    export_group = parser.add_argument_group('export options', 'Control what files to generate')
    export_group.add_argument('--no-gpx', action='store_true', help='Skip GPX file generation')
    export_group.add_argument('--no-map', action='store_true', help='Skip HTML map generation')
    export_group.add_argument('--no-summary', action='store_true', help='Skip summary markdown generation')
    export_group.add_argument('--no-data', action='store_true', help='Skip JSON data export')
    
    args = parser.parse_args()
    
    if args.via and args.roundtrip:
        print("Error: Cannot use both --via and --roundtrip. Use --via for a multi-city route with variety.")
        return 1
    
    if not GOOGLE_PLACES_API_KEY:
        print("Error: GOOGLE_PLACES_API_KEY not found in .env file")
        return 1
    
    # Create trip configuration from arguments
    trip_config = TripConfig(
        search_hotels=not args.no_hotels,
        pet_friendly_only=not args.all_hotels,
        search_vets=not args.no_vets,
        search_national_parks=not args.no_national_parks,
        search_monuments=not args.no_monuments,
        search_parks=not args.no_parks,
        search_museums=not args.no_museums,
        search_restaurants=not args.no_restaurants,
        search_dog_parks=not args.no_dog_parks,
        search_viewpoints=not args.no_viewpoints,
        search_ev_chargers=not args.no_ev_chargers,
        export_gpx=not args.no_gpx,
        export_map=not args.no_map,
        export_summary=not args.no_summary,
        export_data=not args.no_data
    )
    
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
    
    # Select strategic stop cities based on driving hours
    # Average highway speed ~65 mph, so 8 hours ≈ 520 miles
    target_miles = args.target_hours * 65  # Approximate highway speed
    print(f"🎯 Selecting major stop cities (~{args.target_hours} hours/{target_miles} miles apart)...")
    major_stops = []
    
    # Add origin with Wikivoyage link
    city_name_only = args.origin.split(',')[0].strip()
    wikivoyage_url = WikipediaHelper.search_wikivoyage(city_name_only)
    
    start_location = {
        'name': args.origin,
        'lat': origin_lat,
        'lon': origin_lon,
        'type': 'start',
        'stop_number': 0,
        'wikivoyage_url': wikivoyage_url,
        'is_major_stop': True
    }
    major_stops.append(start_location)
    
    # Select major stops from cities found along route
    waypoint_cities = []
    if all_cities:
        last_major_lat, last_major_lon = origin_lat, origin_lon
        last_waypoint_lat, last_waypoint_lon = origin_lat, origin_lon
        target_distance_m = target_miles * 1609.34  # Convert miles to meters
        waypoint_distance_m = args.waypoint_interval * 1609.34  # Waypoint interval
        stop_num = 1
        
        for city in all_cities:
            # Calculate distance from last major stop
            dist_from_major = router._haversine_distance(
                (last_major_lat, last_major_lon),
                (city['lat'], city['lon'])
            ) * 1609.34  # Convert to meters
            dist_mi_major = dist_from_major / 1609.34
            
            # Calculate distance from last waypoint
            dist_from_waypoint = router._haversine_distance(
                (last_waypoint_lat, last_waypoint_lon),
                (city['lat'], city['lon'])
            ) * 1609.34
            dist_mi_waypoint = dist_from_waypoint / 1609.34
            
            # Add city as major stop if it's roughly the target distance from last major stop
            if dist_from_major >= target_distance_m * 0.8:  # At least 80% of target
                city_name_only = city['name'].split(',')[0].strip()
                wikivoyage_url = WikipediaHelper.search_wikivoyage(city_name_only)
                
                major_stops.append({
                    'name': city['name'],
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'type': 'major_stop',
                    'stop_number': stop_num,
                    'wikivoyage_url': wikivoyage_url,
                    'is_major_stop': True
                })
                print(f"  Major Stop {stop_num}: {city['name']} (~{dist_mi_major:.0f} mi from last major stop)")
                last_major_lat, last_major_lon = city['lat'], city['lon']
                last_waypoint_lat, last_waypoint_lon = city['lat'], city['lon']  # Reset waypoint tracker
                stop_num += 1
            # Add as waypoint if far enough from last waypoint but not a major stop
            elif dist_from_waypoint >= waypoint_distance_m * 0.8:
                waypoint_cities.append({
                    'name': city['name'],
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'type': 'waypoint',
                    'is_major_stop': False
                })
                last_waypoint_lat, last_waypoint_lon = city['lat'], city['lon']
    
    # Add destination
    dest_city_name = args.destination.split(',')[0].strip()
    dest_wikivoyage = WikipediaHelper.search_wikivoyage(dest_city_name)
    
    major_stops.append({
        'name': args.destination,
        'lat': dest_lat,
        'lon': dest_lon,
        'type': 'destination',
        'stop_number': len(major_stops),
        'wikivoyage_url': dest_wikivoyage,
        'is_major_stop': True
    })
    print(f"  Destination: {args.destination}")
    
    # Add via cities and return if multi-city route
    if via_cities:
        for via in via_cities:
            via_city_name = via['name'].split(',')[0].strip()
            via_wikivoyage = WikipediaHelper.search_wikivoyage(via_city_name)
            
            major_stops.append({
                'name': via['name'],
                'lat': via['lat'],
                'lon': via['lon'],
                'type': 'via',
                'stop_number': len(major_stops),
                'wikivoyage_url': via_wikivoyage,
                'is_major_stop': True
            })
            print(f"  Via: {via['name']}")
        
        major_stops.append({
            'name': f"{args.origin} (return)",
            'lat': origin_lat,
            'lon': origin_lon,
            'type': 'return',
            'stop_number': len(major_stops),
            'wikivoyage_url': wikivoyage_url,  # Reuse origin's wikivoyage
            'is_major_stop': True
        })
        print(f"  Return to: {args.origin}")
    elif args.roundtrip:
        major_stops.append({
            'name': f"{args.origin} (return)",
            'lat': origin_lat,
            'lon': origin_lon,
            'type': 'return',
            'stop_number': len(major_stops),
            'wikivoyage_url': wikivoyage_url,  # Reuse origin's wikivoyage
            'is_major_stop': True
        })
        print(f"  Return to: {args.origin}")
    
    print()
    print(f"✓ Selected {len(major_stops)} major stops")
    if waypoint_cities:
        print(f"✓ Found {len(waypoint_cities)} waypoint cities (hotel-only options every ~{args.waypoint_interval} miles)")
    print()
    
    # Combine all cities that need hotels
    all_hotel_cities = major_stops + waypoint_cities
    
    # Find hotels for major stops AND waypoint cities
    hotels = {}
    waypoint_hotels = {}
    
    if trip_config.search_hotels:
        hotel_type = "pet-friendly hotels" if trip_config.pet_friendly_only else "hotels"
        print(f"🏨 Finding top {hotel_type}...")
        print(f"  Searching {len(major_stops)} major stops...")
        
        # Search hotels for major stops
        for stop in major_stops:
            if stop['type'] in ['start', 'major_stop', 'destination', 'via', 'return']:
                print(f"  {stop['name']}...")
                hotel = places_finder.find_pet_friendly_hotel(
                    stop['name'],
                    stop['lat'],
                    stop['lon'],
                    pet_friendly_only=trip_config.pet_friendly_only
                )
                if hotel:
                    hotels[stop['name']] = hotel
                    print(f"    ✓ {hotel.name} ({hotel.rating}⭐, {hotel.user_ratings_total} reviews)")
                else:
                    print(f"    ⚠ No hotels found")
                time.sleep(1)
        
        # Search hotels for waypoint cities
        if waypoint_cities:
            print(f"  Searching {len(waypoint_cities)} waypoint cities...")
            for waypoint in waypoint_cities:
                print(f"  {waypoint['name']}...")
                hotel = places_finder.find_pet_friendly_hotel(
                    waypoint['name'],
                    waypoint['lat'],
                    waypoint['lon'],
                    pet_friendly_only=trip_config.pet_friendly_only
                )
                if hotel:
                    waypoint_hotels[waypoint['name']] = hotel
                    print(f"    ✓ {hotel.name} ({hotel.rating}⭐)")
                else:
                    print(f"    ⚠ No hotels found")
                time.sleep(1)
        print()
    else:
        print(f"⊘ Hotel search disabled")
        print()
    
    # Find vets for major stops only
    vets = {}
    if trip_config.search_vets:
        print(f"🏥 Finding 24/7 emergency veterinarians...")
        for stop in major_stops:
            if stop['type'] in ['start', 'major_stop', 'destination', 'via']:
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
    else:
        print(f"⊘ Emergency vet search disabled")
        print()
    
    # Find all attractions along route and at major stop cities only
    print(f"🎯 Finding attractions and points of interest...")
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
    
    # 0. Find national parks and monuments in each state we pass through
    if trip_config.search_national_parks or trip_config.search_monuments:
        states_visited = set()
        
        # Get states from cities found along route
        for city in all_cities:
            if ', ' in city['name']:
                state_abbrev = city['name'].split(', ')[-1]
                states_visited.add(state_abbrev)
        
        # ALSO get states from our actual stop cities (origin, destination, via cities)
        for stop in major_stops:
            if ', ' in stop['name']:
                state_abbrev = stop['name'].split(', ')[-1].strip()
                # Only add if it looks like a state abbreviation (2 uppercase letters)
                if len(state_abbrev) == 2 and state_abbrev.isupper():
                    states_visited.add(state_abbrev)
        
        # Use module-level state mapping
        for state_abbrev in sorted(states_visited):
            state_name = STATE_ABBREV_TO_NAME.get(state_abbrev, state_abbrev)
            
            if trip_config.search_national_parks:
                if state_abbrev == sorted(states_visited)[0]:  # First state
                    print(f"  🏞️ Finding major national parks by state...")
                print(f"    Searching {state_name}...")
                national_parks = places_finder.find_national_parks_by_state(state_name)
                all_attractions['national_parks'].extend(national_parks)
            
            # Also find monuments in this state
            if trip_config.search_monuments:
                if state_abbrev == sorted(states_visited)[0] and not trip_config.search_national_parks:  # First state
                    print(f"  🗿 Finding monuments by state...")
                monuments = places_finder.find_monuments_by_state(state_name)
                all_attractions['monuments'].extend(monuments)
            time.sleep(1)
    
    # 1. Major parks along the route (tighter criteria)
    if trip_config.search_parks:
        print(f"  🌲 Scanning for major parks along route...")
        route_parks = places_finder.find_parks_along_route(route_geometry)
        all_attractions['parks'].extend(route_parks)
    
    # 2. Scenic viewpoints along the route
    if trip_config.search_viewpoints:
        print(f"  📸 Scanning for scenic viewpoints...")
        viewpoints = places_finder.find_scenic_viewpoints_along_route(route_geometry, sample_interval_miles=25)
        all_attractions['viewpoints'].extend(viewpoints)
    
    # 2.5. EV chargers along the route
    if trip_config.search_ev_chargers:
        print(f"  ⚡ Scanning for EV charging stations along route...")
        route_chargers = places_finder.find_ev_chargers_along_route(
            route_geometry,
            sample_interval_miles=25
        )
        all_attractions['ev_chargers'].extend(route_chargers)
    
    # 3. Attractions at major stop cities
    if any([trip_config.search_parks, trip_config.search_museums, trip_config.search_restaurants, trip_config.search_dog_parks, trip_config.search_ev_chargers]):
        print(f"  Searching near major stop cities...")
        for stop in major_stops:
            if stop['type'] in ['start', 'stop', 'destination', 'via']:
                print(f"    {stop['name']}...")
                
                # Parks at cities
                if trip_config.search_parks:
                    parks = places_finder.find_parks_nearby(stop['name'], stop['lat'], stop['lon'], limit=3)
                    all_attractions['parks'].extend(parks)
                
                # Museums
                if trip_config.search_museums:
                    museums = places_finder.find_museums_in_city(stop['name'], stop['lat'], stop['lon'], limit=3)
                    all_attractions['museums'].extend(museums)
                
                # Dog-friendly restaurants
                if trip_config.search_restaurants:
                    restaurants = places_finder.find_dog_friendly_restaurants(stop['name'], stop['lat'], stop['lon'], limit=5)
                    all_attractions['restaurants'].extend(restaurants)
                
                # Dog parks
                if trip_config.search_dog_parks:
                    dog_parks = places_finder.find_dog_parks_in_city(stop['name'], stop['lat'], stop['lon'], limit=2)
                    all_attractions['dog_parks'].extend(dog_parks)
                
                # EV chargers
                if trip_config.search_ev_chargers:
                    ev_chargers = places_finder.find_ev_chargers_in_city(
                        stop['name'], stop['lat'], stop['lon'],
                        limit=3
                    )
                    all_attractions['ev_chargers'].extend(ev_chargers)
                
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
        unique_attractions.sort(key=lambda a: calculate_popularity_score(a.rating, a.user_ratings_total), reverse=True)
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
    print(f"   ⚡ EV Chargers: {len(all_attractions['ev_chargers'])}")
    print()
    
    # Create output directory
    output_dir = Path("trip routes")
    output_dir.mkdir(exist_ok=True)
    
    # Determine base filename
    if via_cities:
        via_names = '_'.join([via['name'].replace(', ', '_').replace(' ', '_') for via in via_cities])
        output_base = f"trip_{args.origin.replace(', ', '_')}_{args.destination.replace(', ', '_')}_via_{via_names}"
    else:
        output_base = f"trip_{args.origin.replace(', ', '_')}_{args.destination.replace(', ', '_')}"
    output_base = output_base.replace(' ', '_')
    
    # Create map if enabled
    if trip_config.export_map:
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
            major_stops,
            waypoint_cities,
            hotels,
            waypoint_hotels,
            vets,
            all_attractions,
            trip_name,
            route_data
        )
        
        output_file = output_base + ".html"
        output_path = output_dir / output_file
        trip_map.save(str(output_path))
        print(f"  ✓ Map saved: {output_path}")
        print()
    else:
        print(f"⊘ Map generation disabled")
        print()
    
    # Save data if enabled
    if trip_config.export_data:
        trip_data = {
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'origin': args.origin,
            'destination': args.destination,
            'via_cities': [via['name'] for via in via_cities] if via_cities else None,
            'roundtrip': args.roundtrip,
            'total_distance_miles': round(total_distance_mi, 1),
            'total_duration_hours': round(total_duration_h, 1),
            'major_stops': major_stops,
            'waypoint_cities': waypoint_cities,
            'hotels': {city: asdict(hotel) for city, hotel in hotels.items()},
            'waypoint_hotels': {city: asdict(hotel) for city, hotel in waypoint_hotels.items()},
            'vets': {city: asdict(vet) for city, vet in vets.items()},
            'attractions': {
                'national_parks': [asdict(a) for a in all_attractions['national_parks']],
                'monuments': [asdict(a) for a in all_attractions['monuments']],
                'parks': [asdict(a) for a in all_attractions['parks']],
                'museums': [asdict(a) for a in all_attractions['museums']],
                'restaurants': [asdict(a) for a in all_attractions['restaurants']],
                'dog_parks': [asdict(a) for a in all_attractions['dog_parks']],
                'viewpoints': [asdict(a) for a in all_attractions['viewpoints']],
                'ev_chargers': [asdict(a) for a in all_attractions['ev_chargers']]
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
            }
        }
        
        data_file = output_dir / (output_base + "_data.json")
        with open(data_file, 'w') as f:
            json.dump(trip_data, f, indent=2)
        print(f"  ✓ Trip data saved: {data_file}")
    else:
        trip_data = None  # Still need this for summary generation
    
    # Generate GPX file for navigation apps if enabled
    if trip_config.export_gpx:
        print(f"🗺️  Generating GPX file for navigation apps...")
        map_route_geometry = [[coord[1], coord[0]] for coord in route_data['geometry']['coordinates']]
        
        trip_name = f"Road Trip: {args.origin} → {args.destination}"
        if via_cities:
            for via in via_cities:
                trip_name += f" → {via['name']}"
            trip_name += f" → {args.origin}"
        elif args.roundtrip:
            trip_name += f" → {args.origin}"
        
        gpx_file = output_dir / (output_base + ".gpx")
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
        print()
    else:
        print(f"⊘ GPX generation disabled")
        print()
    
    # Generate summary if enabled
    if trip_config.export_summary:
        summary_file = output_dir / (output_base + '_summary.md')
        
        trip_name = f"Road Trip: {args.origin} → {args.destination}"
        if via_cities:
            for via in via_cities:
                trip_name += f" → {via['name']}"
            trip_name += f" → {args.origin}"
        elif args.roundtrip:
            trip_name += f" → {args.origin}"
        
        generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(summary_file, 'w') as f:
            f.write(f"# {trip_name}\n\n")
            f.write(f"*Generated: {generated_time}*\n\n")
            f.write(f"## Trip Overview\n\n")
            f.write(f"- **Distance**: {total_distance_mi:.1f} miles\n")
            f.write(f"- **Estimated Driving Time**: {int(total_duration_h)}h {int((total_duration_h % 1) * 60)}m\n")
            f.write(f"- **Number of Major Stops**: {len(major_stops)}\n")
            f.write(f"- **Number of Waypoint Cities**: {len(waypoint_cities)}\n\n")
        
        f.write(f"## Major Stops\n\n")
        for i, stop in enumerate(major_stops, 1):
            f.write(f"{i}. {stop['name']}\n")
        f.write("\n")
        
        f.write(f"## Waypoint Cities\n\n")
        for i, waypoint in enumerate(waypoint_cities, 1):
            f.write(f"{i}. {waypoint['name']}\n")
        f.write("\n")
        
        f.write(f"## Hotels at Major Stops ({len(hotels)} found)\n\n")
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
        
        f.write(f"## Hotels at Waypoint Cities ({len(waypoint_hotels)} found)\n\n")
        for city, hotel in waypoint_hotels.items():
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
    else:
        print(f"⊘ Summary generation disabled")
        print()
    
    print("="*70)
    print("✅ TRIP PLANNING COMPLETE!")
    print("="*70)
    print()
    
    # Print generated files
    if any([trip_config.export_map, trip_config.export_gpx, trip_config.export_data, trip_config.export_summary]):
        print(f"📂 Files generated:")
        if trip_config.export_map:
            map_file = output_dir / (output_base + ".html")
            print(f"   - {map_file} (interactive map)")
        if trip_config.export_gpx:
            gpx_file = output_dir / (output_base + ".gpx")
            print(f"   - {gpx_file} (GPX route for Magic Earth, OsmAnd, etc.)")
        if trip_config.export_data:
            data_file = output_dir / (output_base + "_data.json")
            print(f"   - {data_file} (trip data)")
        if trip_config.export_summary:
            summary_file = output_dir / (output_base + "_summary.md")
            print(f"   - {summary_file} (summary report)")
        print()
        
        # Print helpful messages based on what was exported
        if trip_config.export_map:
            map_file = output_dir / (output_base + ".html")
            print(f"🎉 Open {map_file} in your browser to explore your trip!")
        if trip_config.export_gpx:
            gpx_file = output_dir / (output_base + ".gpx")
            print(f"📱 Import {gpx_file} to your navigation app!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

