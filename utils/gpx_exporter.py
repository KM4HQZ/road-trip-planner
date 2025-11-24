"""GPX export utilities for importing routes into navigation apps."""

from typing import List, Dict
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom


def create_gpx_file(
    route_geometry: List[List[float]],
    major_stops: List[Dict],
    waypoint_cities: List[Dict],
    hotels: Dict,
    waypoint_hotels: Dict,
    vets: Dict,
    attractions: Dict,
    trip_name: str,
    output_path: str
) -> None:
    """
    Create a GPX file from trip data for import into navigation apps.
    
    GPX files are compatible with:
    - Magic Earth
    - OsmAnd
    - Maps.me
    - Organic Maps
    - Google Maps (import)
    - Most GPS devices
    
    Args:
        route_geometry: List of [lat, lon] coordinates from route
        major_stops: List of major stop city dicts
        waypoint_cities: List of waypoint city dicts
        hotels: Dict of hotels at major stops
        waypoint_hotels: Dict of hotels at waypoints
        vets: Dict of veterinarians
        attractions: Dict of attraction lists by category
        trip_name: Name of the trip
        output_path: Path to save GPX file
    """
    # Create GPX root element
    gpx = ET.Element('gpx', {
        'version': '1.1',
        'creator': 'Road Trip Planner',
        'xmlns': 'http://www.topografix.com/GPX/1/1',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd'
    })
    
    # Add metadata
    metadata = ET.SubElement(gpx, 'metadata')
    name = ET.SubElement(metadata, 'name')
    name.text = trip_name
    
    desc = ET.SubElement(metadata, 'desc')
    desc.text = f'Pet-friendly road trip generated on {datetime.now().strftime("%Y-%m-%d")}'
    
    time = ET.SubElement(metadata, 'time')
    time.text = datetime.now().isoformat()
    
    # Add major stops as waypoints
    for i, stop in enumerate(major_stops):
        wpt = ET.SubElement(gpx, 'wpt', {
            'lat': str(stop['lat']),
            'lon': str(stop['lon'])
        })
        
        wpt_name = ET.SubElement(wpt, 'name')
        wpt_name.text = f"Stop {i}: {stop['name']}"
        
        wpt_desc = ET.SubElement(wpt, 'desc')
        desc_parts = [f"Major stop on your road trip"]
        
        # Add hotel info if available
        if stop['name'] in hotels:
            hotel = hotels[stop['name']]
            desc_parts.append(f"Hotel: {hotel.name} ({hotel.rating}⭐)")
        
        # Add vet info if available
        if stop['name'] in vets:
            vet = vets[stop['name']]
            vet_status = "24/7" if vet.is_24_hours else "Regular hours"
            desc_parts.append(f"Vet: {vet.name} ({vet_status})")
        
        if stop.get('wikivoyage_url'):
            desc_parts.append(f"Travel guide: {stop['wikivoyage_url']}")
        
        wpt_desc.text = ' | '.join(desc_parts)
        
        wpt_type = ET.SubElement(wpt, 'type')
        wpt_type.text = 'Major Stop'
    
    # Add waypoint cities as waypoints (optional stops)
    for i, waypoint in enumerate(waypoint_cities):
        wpt = ET.SubElement(gpx, 'wpt', {
            'lat': str(waypoint['lat']),
            'lon': str(waypoint['lon'])
        })
        
        wpt_name = ET.SubElement(wpt, 'name')
        wpt_name.text = f"Waypoint: {waypoint['name']}"
        
        wpt_desc = ET.SubElement(wpt, 'desc')
        desc_parts = ["Optional stop with hotel available"]
        
        if waypoint['name'] in waypoint_hotels:
            hotel = waypoint_hotels[waypoint['name']]
            desc_parts.append(f"Hotel: {hotel.name} ({hotel.rating}⭐)")
        
        wpt_desc.text = ' | '.join(desc_parts)
        
        wpt_type = ET.SubElement(wpt, 'type')
        wpt_type.text = 'Waypoint'
    
    # Add hotels as POI waypoints
    for city_name, hotel in hotels.items():
        wpt = ET.SubElement(gpx, 'wpt', {
            'lat': str(hotel.lat),
            'lon': str(hotel.lon)
        })
        
        wpt_name = ET.SubElement(wpt, 'name')
        wpt_name.text = f"🏨 {hotel.name}"
        
        wpt_desc = ET.SubElement(wpt, 'desc')
        wpt_desc.text = f"Pet-friendly hotel | {hotel.rating}⭐ ({hotel.user_ratings_total} reviews) | {hotel.address}"
        
        if hotel.phone:
            wpt_desc.text += f" | Phone: {hotel.phone}"
        
        wpt_type = ET.SubElement(wpt, 'type')
        wpt_type.text = 'Lodging'
    
    # Add waypoint hotels
    for city_name, hotel in waypoint_hotels.items():
        wpt = ET.SubElement(gpx, 'wpt', {
            'lat': str(hotel.lat),
            'lon': str(hotel.lon)
        })
        
        wpt_name = ET.SubElement(wpt, 'name')
        wpt_name.text = f"🏨 {hotel.name} (Waypoint)"
        
        wpt_desc = ET.SubElement(wpt, 'desc')
        wpt_desc.text = f"Pet-friendly hotel | {hotel.rating}⭐ | {hotel.address}"
        
        wpt_type = ET.SubElement(wpt, 'type')
        wpt_type.text = 'Lodging'
    
    # Add emergency vets
    for city_name, vet in vets.items():
        wpt = ET.SubElement(gpx, 'wpt', {
            'lat': str(vet.lat),
            'lon': str(vet.lon)
        })
        
        wpt_name = ET.SubElement(wpt, 'name')
        vet_emoji = "🏥⏰" if vet.is_24_hours else "🏥"
        wpt_name.text = f"{vet_emoji} {vet.name}"
        
        wpt_desc = ET.SubElement(wpt, 'desc')
        hours = "24/7 Emergency" if vet.is_24_hours else "Regular hours"
        wpt_desc.text = f"Veterinarian | {hours} | {vet.rating}⭐ ({vet.user_ratings_total} reviews) | {vet.address}"
        
        if vet.phone:
            wpt_desc.text += f" | Phone: {vet.phone}"
        
        wpt_type = ET.SubElement(wpt, 'type')
        wpt_type.text = 'Medical'
    
    # Add selected attractions (top-rated ones to avoid overwhelming the file)
    attraction_limits = {
        'national_parks': 10,
        'monuments': 5,
        'parks': 10,
        'museums': 5,
        'restaurants': 10,
        'dog_parks': 10,
        'viewpoints': 10
    }
    
    attraction_emojis = {
        'national_parks': '🏞️',
        'monuments': '🗿',
        'parks': '🌲',
        'museums': '🏛️',
        'restaurants': '🍽️',
        'dog_parks': '🐾',
        'viewpoints': '📸'
    }
    
    for category, attraction_list in attractions.items():
        limit = attraction_limits.get(category, 5)
        emoji = attraction_emojis.get(category, '📍')
        
        for attraction in attraction_list[:limit]:
            wpt = ET.SubElement(gpx, 'wpt', {
                'lat': str(attraction.lat),
                'lon': str(attraction.lon)
            })
            
            wpt_name = ET.SubElement(wpt, 'name')
            wpt_name.text = f"{emoji} {attraction.name}"
            
            wpt_desc = ET.SubElement(wpt, 'desc')
            desc_text = f"{category.replace('_', ' ').title()} | {attraction.rating}⭐ ({attraction.user_ratings_total} reviews)"
            
            if hasattr(attraction, 'address') and attraction.address:
                desc_text += f" | {attraction.address}"
            
            wpt_desc.text = desc_text
            
            wpt_type = ET.SubElement(wpt, 'type')
            wpt_type.text = category.replace('_', ' ').title()
    
    # Add the route as a track
    trk = ET.SubElement(gpx, 'trk')
    
    trk_name = ET.SubElement(trk, 'name')
    trk_name.text = f"{trip_name} - Route"
    
    trk_desc = ET.SubElement(trk, 'desc')
    trk_desc.text = "Full driving route along actual roads"
    
    # Create track segment
    trkseg = ET.SubElement(trk, 'trkseg')
    
    # Add all route points (coordinates are [lat, lon] format)
    for coord in route_geometry:
        trkpt = ET.SubElement(trkseg, 'trkpt', {
            'lat': str(coord[0]),
            'lon': str(coord[1])
        })
    
    # Pretty print and save
    xml_str = minidom.parseString(ET.tostring(gpx, encoding='unicode')).toprettyxml(indent='  ')
    
    # Remove extra blank lines
    xml_lines = [line for line in xml_str.split('\n') if line.strip()]
    xml_str = '\n'.join(xml_lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"  ✓ GPX file saved: {output_path}")
    print(f"    Compatible with Magic Earth, OsmAnd, Maps.me, Organic Maps, and more!")
