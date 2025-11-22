# Dynamic Pet-Friendly Road Trip Planner 🚗🐾

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

An intelligent road trip planning tool that automatically finds pet-friendly hotels, emergency vets, parks, restaurants, and attractions for multi-city road trips.

## 🌟 What This Does

- 🏨 **Finds pet-friendly hotels** at strategic stops (rated by score)
- 🏥 **Locates 24/7 emergency vets** at each major city
- 🌲 **Discovers parks** along your entire route (with tighter radius for roadside stops)
- 🏛️ **Finds museums & cultural attractions** in stop cities
- 🍽️ **Locates dog-friendly restaurants** with outdoor seating
- � **Finds dog parks** for exercise breaks
- 📸 **Identifies scenic viewpoints** along the way
- 🗺️ **Creates interactive maps** with different icons for each attraction type
- � **Generates detailed reports** in Markdown and JSON formats
- 🛣️ **Uses actual road routes** with accurate distances and driving times

## 🎯 Key Features

### Two-Tiered Discovery System
- **Along Route**: Samples every 25-75 miles with tight 10km radius for parks/viewpoints
- **At Stop Cities**: Searches 40km radius for comprehensive city exploration

### Intelligent Route Planning
- **City-based stops**: Finds actual cities ~250 miles apart (not random coordinates)
- **Multi-city routes**: Add unlimited waypoints for varied return routes
- **Smart filtering**: Only major parks (4.5+ stars, 500+ reviews) along route
- **Deduplication**: Automatically removes duplicate attractions

### Pet-First Design
- Prioritizes 24/7 vets with 1.5x score boost
- Searches explicitly for "dog friendly" restaurants
- Finds dedicated dog parks at each stop city
- All hotels from trusted pet-friendly chains

## � Services Used

1. **Google Places API (New)** - Hotels, restaurants, vets, attractions, ratings
2. **OpenStreetMap (Nominatim)** - City geocoding and reverse geocoding
3. **OSRM (Open Source Routing Machine)** - Actual road routes and geometry
4. **Folium** - Interactive map generation with layers

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/mort/Documents/road-trip
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Up Google Places API

Create a `.env` file:
```bash
GOOGLE_PLACES_API_KEY=your_api_key_here
```

**Get your API key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Places API (New)"
3. Enable billing (required, but generous free tier)
4. Create API key

### 3. Plan Your Trip!

**Activate virtual environment:**
```bash
source venv/bin/activate
```

## 📋 Usage Examples

### Simple One-Way Trip
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL"
```

### Triangle Route (Different Way Back)
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL" --via "Nashville, TN"
```

### Multi-City Adventure
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL" --via "Nashville, TN" --via "Memphis, TN"
```

Add as many `--via` cities as you want!

### Custom Stop Distance
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL" --stop-distance 200
# Stops every ~200 miles instead of default 250
```

### Old-Style Round Trip (Not Recommended)
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL" --roundtrip
# Takes same route back - use --via instead for variety!
```

## 📂 Output Files

Each trip generates three files:

### 1. Interactive Map (HTML)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_Memphis_TN.html`

- 🗺️ Blue route line following actual highways
- 📍 Red markers for stop cities
- 🏨 Purple markers for hotels
- 🏥 Dark red markers for emergency vets
- 🌲 Green tree icons for parks
- 🏛️ Purple building icons for museums
- 🍽️ Orange fork icons for dog-friendly restaurants
- 🐾 Light green paw icons for dog parks
- 📸 Blue camera icons for scenic viewpoints
- Layer controls to toggle each type on/off

### 2. Trip Data (JSON)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_Memphis_TN_data.json`

Complete structured data including:
- All stops with coordinates
- Hotel details (name, rating, reviews, phone, website)
- Vet details (name, rating, 24/7 status, phone)
- All attractions by category with ratings

### 3. Summary Report (Markdown)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_Memphis_TN_summary.md`

Human-readable summary with:
- Trip overview (distance, time, route)
- Stop cities list
- Hotel recommendations with full details
- Emergency vet locations
- Categorized attractions (parks, museums, restaurants, dog parks, viewpoints)

## � Attraction Categories

### 🌲 Parks
- **Along Route**: 4.5+ stars, 500+ reviews (major parks only)
- **At Cities**: 4.0+ stars, 50+ reviews (top 3 per city)
- Examples: National parks, state parks, botanical gardens

### 🏛️ Museums & Cultural Attractions
- **At Cities Only**: 4.0+ stars, 100+ reviews (top 3 per city)
- Examples: Art museums, historical sites, science centers

### 🍽️ Dog-Friendly Restaurants
- **At Cities Only**: 4.0+ stars, 50+ reviews (top 5 per city)
- **Explicit search**: "dog friendly restaurant" (not just outdoor seating)
- Examples: Breweries with patios, pet-friendly cafes

### 🐾 Dog Parks
- **At Cities Only**: 4.0+ stars (top 2 per city)
- Dedicated off-leash areas for exercise

### 📸 Scenic Viewpoints
- **Along Route**: 4.5+ stars, sampled every 75 miles
- Examples: Overlooks, vista points, observation decks

## 🏨 Hotel Selection

**Pet-Friendly Chains Searched:**
La Quinta, Drury Inn, Red Roof Inn, Motel 6, Best Western, Kimpton, Aloft, Extended Stay, Candlewood Suites, Residence Inn, TownePlace Suites, Homewood Suites, Hampton Inn, Hilton, Hyatt, Marriott, Sheraton, Westin, and more!

**Scoring Formula:**
```
score = rating × log₁₀(reviews + 1)
```
Balances high ratings with popularity.

## 🏥 Emergency Vet Verification

The system strictly verifies 24/7 status:
1. Checks `regularOpeningHours.weekdayDescriptions` for "Open 24 hours" on all 7 days
2. Checks periods structure for continuous operation
3. Falls back to name checking only if no hours data available
4. Marks as "Regular hours" if not confirmed 24/7

**Score Boost:** 24/7 vets get 1.5x score multiplier for prioritization.

## 📊 Example Results

**Atlanta → Chicago → Nashville → Memphis → Atlanta**
- Distance: 1,745.7 miles
- Driving Time: ~33 hours
- Strategic Stops: 10 cities
- Attractions Found: 217 total
  - 129 Parks
  - 25 Museums
  - 43 Dog-friendly restaurants
  - 16 Dog parks
  - 4 Scenic viewpoints
- 24/7 Vets: 4 confirmed (Atlanta, Chicago, Nashville, Memphis)

## 🔍 Legacy Validation Tools

The original static itinerary validation tools are still available:

- `validate_locations.py` - Validate pre-defined itinerary
- `calculate_routes.py` - Calculate routes from itinerary
- `enrich_data.py` - Add Wikipedia data
- `generate_report.py` - Create validation reports
- `filter_hotels.py` - Filter hotel list by ratings
- `run_validation.sh` - Run complete validation pipeline

See bottom of this README for legacy tool documentation.

---

## 🛠️ Legacy Tool Documentation

*(The original static itinerary validation scripts are preserved below)*

### Original Purpose
This toolkit validates a pre-written road trip itinerary using **100% free, open-source services**.

### Legacy Scripts

- `validate_locations.py` - Verify all locations exist and get coordinates
- `calculate_routes.py` - Get accurate driving times between points
- `enrich_data.py` - Add Wikipedia context to locations
- `generate_report.py` - Create comprehensive validation reports
- `filter_hotels.py` - Filter hotel list by ratings
- `run_validation.sh` - Run complete pipeline automatically

### Running the Legacy Pipeline

**First, activate the virtual environment:**
```bash
source venv/bin/activate
```

**Then run the validation:**
```bash
./run_validation.sh
```

This will:
1. Validate all locations from a static itinerary file
2. Calculate actual routes and travel times
3. Enrich with Wikipedia data
4. Generate reports
5. Create an interactive map

### Individual Legacy Script Usage

**Validate Locations**
```bash
python validate_locations.py ../road-trip-itinerary.md
```

Extracts and validates hotels, cities, parks, and gas stops from a markdown itinerary.
Output: `validated_locations.json`

**Calculate Routes**
```bash
python calculate_routes.py
```

Calculates actual driving distances and times between stops.
Output: `calculated_routes.json`

**Enrich Data**
```bash
python enrich_data.py
```

Adds Wikipedia descriptions and images.
Output: `enriched_locations.json`

**Generate Report**
```bash
python generate_report.py
```

Creates validation reports.
Outputs: `validation_report.md`, `validation_report.html`

**Create Map**
```bash
python create_map.py
```

Generates interactive HTML map with all validated locations.
Output: `road_trip_map.html`

**Filter Hotels**
```bash
python filter_hotels.py
```

Filters hotels by Google Places ratings (requires API key in `.env`).
Output: Console output with top-rated hotels per location.

### Legacy Output Files

After running the validation pipeline:

```
road-trip/
├── validated_locations.json     # All locations with coordinates
├── calculated_routes.json       # Route segments with distances/times
├── enriched_locations.json      # Wikipedia data for locations
├── validation_report.md         # Markdown report
├── validation_report.html       # HTML report (open in browser)
├── road_trip_map.html          # Interactive map (open in browser)
└── location_cache.json         # Cache to avoid re-querying APIs
```

### API Rate Limits

All legacy services are free but have rate limits:

- **Nominatim (OSM)**: 1 request/second (built-in 1s delay)
- **OSRM**: No hard limit (please be respectful)
- **Wikipedia**: No hard limit (built-in 0.5s delay)

### Troubleshooting

**Python externally-managed-environment error**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**"Location not found" errors**
- Names might differ slightly in OSM database
- Check validation report for failed items
- Adjust names if needed

**Missing dependencies**
```bash
source venv/bin/activate
pip install --upgrade requests beautifulsoup4 markdown geopy folium pandas tabulate python-dotenv
```

---

**Happy Road Tripping! 🚗🐾**
- Driving time
- Compares with itinerary estimates

Output: `calculated_routes.json`

### Enrich Location Data

```bash
python enrich_data.py
```

Adds for cities and major attractions:
- Wikipedia summaries
- Images
- Links to full articles

Output: `enriched_locations.json`

### Generate Reports

```bash
python generate_report.py
```

Creates:
- `validation_report.md` - Markdown version
- `validation_report.html` - Nicely formatted HTML version

### Create Interactive Map

```bash
python create_map.py
```

Generates `road_trip_map.html` with:
- All locations marked with appropriate icons
- Route lines with distances/times
- Toggle layers (cities, hotels, parks)
- Measure tool for custom distances
- Wikipedia info in popups

## 📊 Output Files

After running the validation:

```
road-trip/
├── validated_locations.json     # All locations with coordinates
├── calculated_routes.json       # Route segments with distances/times
├── enriched_locations.json      # Wikipedia data for locations
├── validation_report.md         # Markdown report
├── validation_report.html       # HTML report (open in browser)
├── road_trip_map.html          # Interactive map (open in browser)
└── location_cache.json         # Cache to avoid re-querying APIs
```

## ⚙️ API Rate Limits

All services are free but have rate limits to prevent abuse:

- **Nominatim (OSM)**: 1 request/second (built-in 1s delay in script)
- **OSRM**: No hard limit (please be respectful)
- **Wikipedia**: No hard limit (built-in 0.5s delay)

The scripts automatically handle rate limiting for you.

## 🔍 What Gets Validated

From your itinerary, the toolkit extracts and validates:

### Hotels (Examples)
- La Quinta Inn & Suites Memphis Downtown
- Aloft Oklahoma City Downtown
- Drury Inn & Suites Colorado Springs
- The Cosmopolitan Las Vegas

### Cities
- Memphis, TN
- Oklahoma City, OK
- Colorado Springs, CO
- Flagstaff, AZ
- Las Vegas, NV

### Parks & Attractions
- Oak Mountain State Park
- Palo Duro Canyon State Park
- Garden of the Gods
- Red Rock Canyon
- Grand Canyon South Rim

### Gas Stops
- Birmingham, AL
- Amarillo, TX
- Barstow, CA

## 🛠️ Troubleshooting

### Python externally-managed-environment error

On Debian/Ubuntu systems, you may see:
```
error: externally-managed-environment
```

**Solution**: Use a virtual environment (already set up if you followed the installation steps):
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Location not found" errors

Some hotels/locations might not validate if:
- Name is slightly different in OSM (e.g., "La Quinta Inn" vs "La Quinta Inn & Suites")
- Very new location not yet in OSM database
- Need more specific address

**Solution**: Check the validation report for failed items and adjust names if needed.

### Folium tile layer errors

If you see errors about tile attributions:
```
ValueError: Custom tiles must have an attribution.
```

This is due to newer versions of Folium requiring proper attribution for tile layers. The script has been updated to handle this automatically.

### API timeout errors

If you see timeouts:
- Check your internet connection
- Wait a minute and try again (temporary API issues)
- The script will cache successful results, so you won't re-query them

### Missing dependencies

If you see import errors, make sure the virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install --upgrade requests beautifulsoup4 markdown geopy folium pandas tabulate
```

## 📝 Example Output

After validation, you'll see:

```
VALIDATION SUMMARY
═══════════════════════════════════════════════════════════════════
Total locations: 127
Successfully validated: 118 (92.9%)
Failed validation: 9 (7.1%)

By Type:
  city: 45/45 validated
  hotel: 56/62 validated
  park: 17/20 validated
```

## 🗺️ Interactive Map Features

The generated map includes:

- **Road-focused design**: Default view optimized for highway and route planning
- **70 validated locations** marked with different colored icons
- **Route visualization**: Highway-style red lines with directional arrows
- **Multiple map layers**: Road Map (default), Light Map, Street Map, and Terrain reference
- **Toggle controls** to show/hide different location types (Cities, Hotels, Parks, Routes)
- **Interactive features**: Click markers for Wikipedia descriptions, click routes for distance/time info
- **Measure tool** for calculating custom distances
- **Fullscreen mode** for detailed exploration

## 🗺️ Map Layer Options

- **Road Map (Default)**: Optimized for road trips with clear highway visibility
- **Light Map**: Clean, minimal view focusing on routes
- **Street Map**: Detailed street-level view
- **Terrain (Reference)**: Topographic view for geographic context

## 💡 Tips

1. **Cache**: Results are cached in `location_cache.json`. Delete this file if you want to re-query everything.

2. **Partial runs**: You can run scripts individually. Each depends on the previous:
   - `validate_locations.py` (required first)
   - `calculate_routes.py` (needs validated locations)
   - `enrich_data.py` (needs validated locations)
   - `generate_report.py` (uses all above data)
   - `create_map.py` (uses all above data)

3. **Updates**: If you modify the itinerary, just re-run the validation pipeline.

4. **Browser**: For best map experience, use Chrome, Firefox, or Edge.

## 🎁 Bonus Features

- Route segments show difference between calculated and itinerary estimates
- Failed validations are clearly marked for manual review
- Wikipedia summaries help you learn about stops along the way
- Interactive map is shareable (just send the HTML file)

## 📞 No External Services Required

Everything runs locally on your machine. The only external calls are to:
- OpenStreetMap (public, free)
- OSRM (public, free)  
- Wikipedia (public, free)

No API keys, no sign-ups, no costs!

---

## 📄 License

This project is dual-licensed:

### For Non-Commercial Use
Licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

**You are free to:**
- ✅ Share — copy and redistribute the material
- ✅ Adapt — remix, transform, and build upon the material

**Under these terms:**
- 📝 **Attribution** — Give appropriate credit and link to the license
- 🚫 **NonCommercial** — Cannot be used for commercial purposes
- 🔄 **ShareAlike** — Distribute modifications under the same license

### For Commercial Use
Please contact the author for commercial licensing options.

---

**Happy Road Tripping! 🚗🐾**
**Happy Road Tripping! 🚗🐕🐕**
