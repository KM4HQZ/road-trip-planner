"""Map generation utilities for the road trip planner."""

import folium
from folium import plugins
from typing import List, Dict
from datetime import datetime
from models import Hotel, Veterinarian
from utils.distance import haversine_distance


def create_trip_map(
    route_geometry: List[List[float]],
    stops: List[Dict],
    hotels: Dict[str, Hotel],
    vets: Dict[str, Veterinarian],
    attractions: Dict[str, List],
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
        popup_html = f"<b>{stop['name']}</b><br>Stop #{stop.get('stop_number', '?')}"
        if stop.get('wikivoyage_url'):
            popup_html += f'<br><br><a href="{stop["wikivoyage_url"]}" target="_blank">📚 Wikivoyage Travel Guide</a>'
        
        folium.CircleMarker(
            location=[stop['lat'], stop['lon']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
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
        distance_group = folium.FeatureGroup(name='📏 Distances & Times', show=True)
        stop_cities = [stop for stop in stops if stop['type'] != 'return']
        
        for i in range(len(stop_cities) - 1):
            current_stop = stop_cities[i]
            next_stop = stop_cities[i + 1]
            
            distance_mi = haversine_distance(current_stop['lat'], current_stop['lon'], 
                                           next_stop['lat'], next_stop['lon'], 'miles')
            hours = distance_mi / 60.0
            route_coords = route_geometry
            
            def find_closest_point_index(lat, lon, coords):
                min_dist = float('inf')
                min_idx = 0
                for idx, coord in enumerate(coords):
                    dist = haversine_distance(lat, lon, coord[0], coord[1], 'miles')
                    if dist < min_dist:
                        min_dist = dist
                        min_idx = idx
                return min_idx
            
            start_idx = find_closest_point_index(current_stop['lat'], current_stop['lon'], route_coords)
            end_idx = find_closest_point_index(next_stop['lat'], next_stop['lon'], route_coords)
            
            mid_idx = (start_idx + end_idx) // 2
            if mid_idx < len(route_coords):
                mid_lat, mid_lon = route_coords[mid_idx][0], route_coords[mid_idx][1]
            else:
                mid_lat = (current_stop['lat'] + next_stop['lat']) / 2
                mid_lon = (current_stop['lon'] + next_stop['lon']) / 2
            
            time_str = f"{int(hours)}h {int((hours % 1) * 60)}m" if hours >= 1 else f"{int(hours * 60)}m"
            
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
    
    attraction_groups = {}
    for attraction_type in icon_config.keys():
        attraction_groups[attraction_type] = folium.FeatureGroup(
            name=f"{icon_config[attraction_type]['emoji']} {attraction_type.replace('_', ' ').title()}s"
        )
    
    for category, attraction_list in attractions.items():
        for attraction in attraction_list:
            if category == 'national_parks':
                config = icon_config['national_park']
                popup_html = f"<b>{config['emoji']} {attraction.name}</b><br>"
                popup_html += f"<b>⭐ {attraction.rating}/5.0</b> ({attraction.user_ratings_total:,} reviews)<br>"
                if attraction.address:
                    popup_html += f"📍 {attraction.address}<br>"
                if hasattr(attraction, 'website') and attraction.website:
                    popup_html += f'<br><a href="{attraction.website}" target="_blank">🔗 Official Website</a>'
                if hasattr(attraction, 'wikipedia_url') and attraction.wikipedia_url:
                    popup_html += f'<br><a href="{attraction.wikipedia_url}" target="_blank">📚 Wikipedia</a>'
                    if hasattr(attraction, 'wikipedia_summary') and attraction.wikipedia_summary:
                        popup_html += f'<br><br><i style="font-size: 0.85em;">{attraction.wikipedia_summary}</i>'
                popup_html += f"<br><br><i>{attraction.state}</i>"
                
                folium.Marker(
                    location=[attraction.lat, attraction.lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{attraction.name} - {attraction.rating}⭐",
                    icon=folium.Icon(color=config['color'], icon=config['icon'], prefix=config['prefix'])
                ).add_to(attraction_groups['national_park'])
            else:
                config = icon_config.get(attraction.type, icon_config['park'])
                
                popup_html = f"<b>{config['emoji']} {attraction.name}</b><br>"
                popup_html += f"<b>⭐ {attraction.rating}/5.0</b> ({attraction.user_ratings_total:,} reviews)<br>"
                if attraction.address:
                    popup_html += f"📍 {attraction.address}<br>"
                if hasattr(attraction, 'website') and attraction.website:
                    popup_html += f'<br><a href="{attraction.website}" target="_blank">🔗 Website</a>'
                if hasattr(attraction, 'wikipedia_url') and attraction.wikipedia_url:
                    popup_html += f'<br><a href="{attraction.wikipedia_url}" target="_blank">📚 Wikipedia</a>'
                    if hasattr(attraction, 'wikipedia_summary') and attraction.wikipedia_summary:
                        popup_html += f'<br><br><i style="font-size: 0.85em;">{attraction.wikipedia_summary}</i>'
                popup_html += f"<br><br><i>{attraction.location}</i>"
                
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
    
    for group in attraction_groups.values():
        group.add_to(m)
    
    # Add controls
    folium.LayerControl(collapsed=False).add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl(position='topleft').add_to(m)
    
    # Add custom "Toggle All" button
    select_all_script = """
    <script>
    window.addEventListener('load', function() {
        var layerControl = document.querySelector('.leaflet-control-layers');
        if (layerControl) {
            var buttonDiv = document.createElement('div');
            buttonDiv.style.padding = '6px 10px';
            buttonDiv.style.backgroundColor = '#fff';
            buttonDiv.style.borderTop = '1px solid #ddd';
            buttonDiv.style.marginTop = '5px';
            
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
            
            toggleButton.onmouseover = function() {
                this.style.backgroundColor = '#e0e0e0';
            };
            toggleButton.onmouseout = function() {
                this.style.backgroundColor = '#f4f4f4';
            };
            
            toggleButton.onclick = function() {
                var overlayInputs = document.querySelectorAll('.leaflet-control-layers-overlays input[type="checkbox"]');
                var allChecked = true;
                
                overlayInputs.forEach(function(input) {
                    if (!input.checked) {
                        allChecked = false;
                    }
                });
                
                overlayInputs.forEach(function(input) {
                    if (allChecked && input.checked) {
                        input.click();
                    } else if (!allChecked && !input.checked) {
                        input.click();
                    }
                });
            };
            
            buttonDiv.appendChild(toggleButton);
            
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
