# Dynamic Pet-Friendly Road Trip Planner 🚗🐾

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

An intelligent road trip planning tool that automatically finds pet-friendly hotels, emergency vets, parks, restaurants, and attractions for multi-city road trips.

> 🗺️ **[View Live Example Trip!](https://km4hqz.github.io/road-trip-planner/)** See an example trip from Atlanta through Colorado Springs, Las Vegas, and Los Angeles.

## 🌟 What This Does

- 🏨 **Finds pet-friendly hotels** at strategic stops (rated by score)
- 🏥 **Locates 24/7 emergency vets** at each major city
- 🏞️ **Discovers national parks** in every state you pass through
- 🗿 **Finds monuments & memorials** in each state along your route
-  **Discovers parks** along your entire route (with tighter radius for roadside stops)
- 🏛️ **Finds museums & cultural attractions** in stop cities
- 🍽️ **Locates dog-friendly restaurants** with outdoor seating
- 🐾 **Finds dog parks** for exercise breaks
- 📸 **Identifies scenic viewpoints** along the way
- 📏 **Shows distances & driving times** between each stop city
- 🗺️ **Creates interactive maps** with different icons for each attraction type
- 📄 **Generates detailed reports** in Markdown and JSON formats
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
- **Distance tracking**: Shows miles and driving time between each stop city

### Interactive Map Features
- **Toggle All Layers**: One-click button to show/hide all map categories at once
- **Distance Markers**: Visual indicators showing miles and hours between stops
- **Customizable Layers**: Show/hide any combination of hotels, vets, parks, monuments, etc.
- **Rich Popups**: Detailed information for every point of interest

### Pet-First Design
- Prioritizes 24/7 vets with 1.5x score boost
- Searches explicitly for "dog friendly" restaurants
- Finds dedicated dog parks at each stop city
- All hotels from trusted pet-friendly chains

## 🛠️ Services Used

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

Copy the example environment file and add your API key:
```bash
cp .env.example .env
# Edit .env and add your API key
```

Your `.env` file should look like:
```bash
GOOGLE_PLACES_API_KEY=your_actual_api_key_here
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

Each trip generates three files in the `trip routes/` directory:

### 1. Interactive Map (HTML)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN.html`

**Map Features:**
- 🗺️ Blue route line following actual highways
- 📍 Blue markers for stop cities
- 🏨 Red bed icons for pet-friendly hotels
- 🏥 Dark red cross icons for emergency vets
- �️ Dark green flag icons for national parks
- 🗿 Gray monument icons for monuments & memorials
- �🌲 Green tree icons for parks
- 🏛️ Purple building icons for museums
- 🍽️ Orange fork icons for dog-friendly restaurants
- 🐾 Light green paw icons for dog parks
- 📸 Blue camera icons for scenic viewpoints
- 📏 Distance & time markers between stop cities
- ☑️ **"Toggle All" button** to show/hide all layers at once
- Layer controls to toggle each category individually
- Fullscreen mode and measure tool

### 2. Trip Data (JSON)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_data.json`

Complete structured data including:
- All stops with coordinates
- Hotel details (name, rating, reviews, phone, website)
- Vet details (name, rating, 24/7 status, phone)
- All attractions by category (national parks, monuments, parks, museums, restaurants, dog parks, viewpoints) with ratings

### 3. Summary Report (Markdown)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_summary.md`

Human-readable summary with:
- Trip overview (distance, time, route)
- Stop cities list
- Hotel recommendations with full details
- Emergency vet locations
- Categorized attractions with ratings and locations

## 🎯 Attraction Categories

### 🏞️ National Parks
- **By State**: Searches each state crossed by the route
- **Criteria**: 4.3+ stars, 1000+ reviews
- Examples: National Parks, National Monuments, National Recreation Areas

### 🗿 Monuments & Memorials
- **By State**: Searches each state crossed by the route
- **Criteria**: 4.0+ stars, 50+ reviews
- Examples: Historical monuments, war memorials, commemorative statues

### 🌲 Parks
- **Along Route**: 4.5+ stars, 500+ reviews (major parks only)
- **At Cities**: 4.0+ stars, 50+ reviews (top 3 per city)
- Examples: State parks, regional parks, botanical gardens

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

## � Tips

1. **Cache**: The script uses Nominatim's geocoding which has a 1 request/second rate limit. Be patient on first runs.

2. **API Key**: Make sure your Google Places API key is set in the `.env` file and has billing enabled (free tier is generous).

3. **Customization**: Adjust `--stop-distance` to change how often you want hotel stops (default is 250 miles).

4. **Multiple Routes**: Use `--via` to create interesting return routes instead of backtracking.

5. **Browser**: For best map experience, use Chrome, Firefox, or Edge.

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

Some cities might not geocode if:
- Name is ambiguous (try adding state: "Springfield, IL" not just "Springfield")
- Very small or remote location
- Spelling is different in OSM database

**Solution**: Use more specific city names with state abbreviations.

### API timeout errors

If you see timeouts:
- Check your internet connection
- Wait a minute and try again (temporary API issues)
- Some services (Nominatim, OSRM) are public and may have intermittent issues

### Missing dependencies

If you see import errors, make sure the virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install --upgrade requests beautifulsoup4 markdown geopy folium pandas tabulate python-dotenv
```

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
