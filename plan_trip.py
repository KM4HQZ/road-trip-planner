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
from utils import haversine_distance, calculate_popularity_score, create_trip_map

# Import configuration
from config import STATE_ABBREV_TO_NAME

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
    
    # Add origin with Wikivoyage link
    city_name_only = args.origin.split(',')[0].strip()
    wikivoyage_url = WikipediaHelper.search_wikivoyage(city_name_only)
    
    start_location = {
        'name': args.origin,
        'lat': origin_lat,
        'lon': origin_lon,
        'type': 'start',
        'stop_number': 0,
        'wikivoyage_url': wikivoyage_url
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
                city_name_only = city['name'].split(',')[0].strip()
                wikivoyage_url = WikipediaHelper.search_wikivoyage(city_name_only)
                
                stops.append({
                    'name': city['name'],
                    'lat': city['lat'],
                    'lon': city['lon'],
                    'type': 'stop',
                    'stop_number': stop_num,
                    'wikivoyage_url': wikivoyage_url
                })
                print(f"  Stop {stop_num}: {city['name']} (~{dist_mi:.0f} mi from last stop)")
                last_stop_lat, last_stop_lon = city['lat'], city['lon']
                stop_num += 1
    
    # Add destination
    dest_city_name = args.destination.split(',')[0].strip()
    dest_wikivoyage = WikipediaHelper.search_wikivoyage(dest_city_name)
    
    stops.append({
        'name': args.destination,
        'lat': dest_lat,
        'lon': dest_lon,
        'type': 'destination',
        'stop_number': len(stops),
        'wikivoyage_url': dest_wikivoyage
    })
    print(f"  Destination: {args.destination}")
    
    # Add via cities and return if multi-city route
    if via_cities:
        for via in via_cities:
            via_city_name = via['name'].split(',')[0].strip()
            via_wikivoyage = WikipediaHelper.search_wikivoyage(via_city_name)
            
            stops.append({
                'name': via['name'],
                'lat': via['lat'],
                'lon': via['lon'],
                'type': 'via',
                'stop_number': len(stops),
                'wikivoyage_url': via_wikivoyage
            })
            print(f"  Via: {via['name']}")
        
        stops.append({
            'name': f"{args.origin} (return)",
            'lat': origin_lat,
            'lon': origin_lon,
            'type': 'return',
            'stop_number': len(stops),
            'wikivoyage_url': wikivoyage_url  # Reuse origin's wikivoyage
        })
        print(f"  Return to: {args.origin}")
    elif args.roundtrip:
        stops.append({
            'name': f"{args.origin} (return)",
            'lat': origin_lat,
            'lon': origin_lon,
            'type': 'return',
            'stop_number': len(stops),
            'wikivoyage_url': wikivoyage_url  # Reuse origin's wikivoyage
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
    
    # Get states from cities found along route
    for city in all_cities:
        if ', ' in city['name']:
            state_abbrev = city['name'].split(', ')[-1]
            states_visited.add(state_abbrev)
    
    # ALSO get states from our actual stop cities (origin, destination, via cities)
    for stop in stops:
        if ', ' in stop['name']:
            state_abbrev = stop['name'].split(', ')[-1].strip()
            # Only add if it looks like a state abbreviation (2 uppercase letters)
            if len(state_abbrev) == 2 and state_abbrev.isupper():
                states_visited.add(state_abbrev)
    
    # Use module-level state mapping
    for state_abbrev in sorted(states_visited):
        state_name = STATE_ABBREV_TO_NAME.get(state_abbrev, state_abbrev)
        print(f"    Searching {state_name}...")
        national_parks = places_finder.find_national_parks_by_state(state_name)
        all_attractions['national_parks'].extend(national_parks)
        
        # Also find monuments in this state
        monuments = places_finder.find_monuments_by_state(state_name)
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
