#!/usr/bin/env python3
"""Test script to debug GPX geometry issue."""

import json
from pathlib import Path

# Load a trip data file to see what's in it
trip_data_file = Path("trip routes/trip_Atlanta_GA_Colorado_Springs_CO_via_Las_Vegas_NV_Los_Angeles_CA_Atlanta_GA_data.json")

if trip_data_file.exists():
    with open(trip_data_file, 'r') as f:
        data = json.load(f)
    
    print(f"Trip: {data.get('origin')} → {data.get('destination')}")
    print(f"\nNumber of major stops: {len(data.get('major_stops', []))}")
    
    # Check if route geometry is stored
    if 'route_geometry' in data:
        print(f"Route geometry points: {len(data['route_geometry'])}")
        print(f"First 5 points: {data['route_geometry'][:5]}")
    else:
        print("⚠️  No route_geometry in data file!")
        print("Available keys:", list(data.keys()))
else:
    print(f"File not found: {trip_data_file}")
