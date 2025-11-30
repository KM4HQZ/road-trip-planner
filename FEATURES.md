# Feature Details 🎯

Complete technical details about the road trip planner's features, search algorithms, and scoring systems.

## Table of Contents

- [Discovery System](#discovery-system)
- [Attraction Categories](#attraction-categories)
- [Hotel Selection](#hotel-selection)
- [Emergency Vet Verification](#emergency-vet-verification)
- [Route Planning](#route-planning)
- [Services Used](#services-used)

## Discovery System

### Two-Tiered Search Strategy

The planner uses two complementary search strategies:

#### Along Route Sampling
- **EV Chargers**: Every 15 miles with 20km radius
- **Parks & Viewpoints**: Every 75 miles with 10km radius
- **Waypoint Cities**: Every ~250 miles (8 hours driving) for potential overnight stops
- **Quality Filter**: Only highly-rated attractions (4.5+ stars, 500+ reviews for parks)

#### At Stop Cities
- **Radius**: 40km from city center
- **Comprehensive**: Hotels, vets, museums, restaurants, dog parks, attractions
- **Quality Filter**: 4.0+ stars minimum (varies by category)
- **Top Results**: Limits per category to avoid information overload

### Smart Deduplication

- Automatically removes duplicate attractions found in multiple searches
- Uses name and location matching to identify duplicates
- Keeps the highest-rated version when duplicates are found

### Distance Tracking

- Calculates actual driving distances using OSRM routing
- Shows driving time estimates between each stop
- Displays cumulative distance and time for entire trip
- Places distance markers on interactive maps

## Attraction Categories

### 🏞️ National Parks

**Search Strategy:**
- By State: Searches each state crossed by the route
- Separate searches for national parks, monuments, recreation areas

**Criteria:**
- Minimum Rating: 4.3 stars
- Minimum Reviews: 1000
- Types: National Park, National Monument, National Recreation Area, National Forest, State Park (if highly rated)

**Examples:**
- Grand Canyon National Park
- Zion National Park
- Great Smoky Mountains National Park
- Yellowstone National Park

### 🗿 Monuments & Memorials

**Search Strategy:**
- By State: Searches each state crossed by the route
- Focuses on historical and commemorative sites

**Criteria:**
- Minimum Rating: 4.0 stars
- Minimum Reviews: 50
- Types: Monument, Memorial, Historical Landmark, Statue

**Examples:**
- Gateway Arch (St. Louis)
- Mount Rushmore
- Lincoln Memorial
- Statue of Liberty

### 🌲 Parks

**Search Strategy:**
- Along Route: Every 75 miles with 10km radius
- At Cities: 40km radius, top 3 per city

**Criteria (Along Route):**
- Minimum Rating: 4.5 stars
- Minimum Reviews: 500
- Major parks only to avoid clutter

**Criteria (At Cities):**
- Minimum Rating: 4.0 stars
- Minimum Reviews: 50
- Top 3 parks per stop city

**Examples:**
- Centennial Park (Atlanta)
- Forest Park (St. Louis)
- Central Park (New York)
- Balboa Park (San Diego)

### 🏛️ Museums & Cultural Attractions

**Search Strategy:**
- At Cities Only: 40km radius
- Top 3 per stop city

**Criteria:**
- Minimum Rating: 4.0 stars
- Minimum Reviews: 100
- Types: Museum, Art Gallery, Science Center, History Museum, Cultural Center

**Examples:**
- Smithsonian Museums (Washington DC)
- Art Institute of Chicago
- Getty Center (Los Angeles)
- Field Museum (Chicago)

### 🍽️ Dog-Friendly Restaurants

**Search Strategy:**
- At Cities Only: 40km radius
- Top 5 per stop city
- Explicit search term: "dog friendly restaurant"

**Criteria:**
- Minimum Rating: 4.0 stars
- Minimum Reviews: 50
- Must explicitly mention dog-friendly or outdoor seating with pets allowed

**Examples:**
- Breweries with outdoor patios
- Pet-friendly cafes
- Restaurants with dog menus
- Outdoor dining establishments

**Note:** The search specifically looks for "dog friendly" restaurants, not just restaurants with outdoor seating. This ensures pet access is explicitly allowed.

### 🐾 Dog Parks

**Search Strategy:**
- At Cities Only: 40km radius
- Top 2 per stop city

**Criteria:**
- Minimum Rating: 4.0 stars
- Type: Dog Park, Off-Leash Dog Area

**Purpose:**
- Exercise breaks for your pet
- Socialization opportunities
- Off-leash play areas

### 📸 Scenic Viewpoints

**Search Strategy:**
- Along Route: Every 75 miles
- Sampled points along the route geometry

**Criteria:**
- Minimum Rating: 4.5 stars
- Types: Viewpoint, Scenic Overlook, Vista Point, Observation Deck, Scenic Drive

**Examples:**
- Mather Point (Grand Canyon)
- Inspiration Point (Bryce Canyon)
- Key West Scenic Overlook
- Rockefeller Center Observation Deck

### ⚡ EV Charging Stations

**Search Strategy:**
- Along Route: Every 15 miles with 20km radius
- At Cities: 40km radius, top 5 per city

**Criteria:**
- No minimum rating or review count (all chargers included)
- All networks: Electrify America, ChargePoint, EVgo, Tesla, etc.

**Map Display:**
- Purple bolts: Electrify America stations
- Light blue bolts: Other charging networks
- Separate toggleable layers for each network

**No Quality Filter:**
Unlike other attractions, EV chargers are not filtered by rating or reviews. All charging stations are included to ensure maximum coverage for electric vehicle travelers.

## Hotel Selection

### Pet-Friendly Chains

The planner searches for hotels from these trusted pet-friendly chains:

**Major Chains:**
- La Quinta Inn & Suites
- Drury Hotels
- Red Roof Inn
- Motel 6
- Best Western
- Kimpton Hotels
- Aloft Hotels
- Extended Stay America
- Candlewood Suites
- Residence Inn
- TownePlace Suites
- Homewood Suites
- Hampton Inn
- Hilton
- Hyatt
- Marriott
- Sheraton
- Westin

### Scoring System

Hotels are ranked using a logarithmic scoring formula that balances rating quality with popularity:

```
score = rating × log₁₀(reviews + 1)
```

**Why This Formula:**
- Prevents new hotels with few reviews from ranking too high
- Rewards popular hotels with many reviews
- Balances quality (rating) with reliability (review count)
- Uses logarithm to prevent review count from dominating

**Example Scores:**
- 5.0 rating, 10 reviews: 5.0 × 1.04 = 5.2
- 4.5 rating, 100 reviews: 4.5 × 2.00 = 9.0
- 4.0 rating, 1000 reviews: 4.0 × 3.00 = 12.0

### All Hotels Mode

When using `--all-hotels` flag (or unchecking "Pet-friendly only" in GUI):
- Searches for all hotels, not just pet-friendly chains
- Useful for finding more options or luxury hotels
- **Warning:** Not all results may accept pets - always call ahead

## Emergency Vet Verification

### 24/7 Status Verification

The planner uses strict verification to confirm true 24/7 emergency vet availability:

#### Primary Verification (Google Places API)
1. **Check `regularOpeningHours.weekdayDescriptions`**
   - Must show "Open 24 hours" for all 7 days
   - Most reliable method

2. **Check `periods` structure**
   - Must show continuous operation (no close times)
   - Verifies no gaps in coverage

3. **Fallback: Name checking**
   - Only if no hours data available
   - Searches for "24 hour", "emergency", "ER" in business name
   - Marks as "verification needed" in results

#### Status Labels
- **"24/7"**: Confirmed open 24 hours via API data
- **"Regular hours"**: Not 24/7 or hours not available
- **"Emergency (verify)"**: Name suggests emergency but hours not confirmed

### Scoring System

Veterinarians use the same base scoring formula as hotels:

```
score = rating × log₁₀(reviews + 1)
```

**24/7 Boost:**
Confirmed 24/7 emergency vets receive a 1.5× score multiplier:

```
if vet.is_24_7:
    score = score × 1.5
```

This prioritizes true emergency vets while still showing highly-rated regular vets if no 24/7 options are available.

**Example Scores:**
- 4.5 rating, 100 reviews, 24/7: 9.0 × 1.5 = 13.5
- 4.8 rating, 200 reviews, regular: 11.0 × 1.0 = 11.0
- The 24/7 vet ranks higher despite slightly lower rating

### Why This Matters

For road trips with pets, knowing you have access to emergency veterinary care is crucial:
- Accidents can happen at any hour
- Sudden illness doesn't wait for business hours
- Peace of mind during long drives
- Critical for multi-day trips through rural areas

## Route Planning

### City-Based Stops

The planner uses actual cities for overnight stops, not arbitrary GPS coordinates:

**Advantages:**
- Real hotels and services available
- Known destinations for navigation
- Wikivoyage travel guides available
- Easier trip planning and communication

**Target Distance:**
- Default: ~250 miles between stops (8 hours driving)
- Configurable with `--target-hours` flag
- Finds nearest city to target distance

### Multi-City Waypoints

Use `--via` flags to create varied return routes:

```bash
python plan_trip.py "Atlanta, GA" "Seattle, WA" --via "Denver, CO" --via "Portland, OR"
```

**Benefits:**
- Different scenery on return trip
- Visit multiple destinations
- Flexible routing for sightseeing
- Avoid backtracking on roundtrips

### Route Geometry

Uses OSRM (Open Source Routing Machine) for actual road routes:
- Follows highways and major roads
- Calculates accurate distances
- Provides turn-by-turn geometry
- Samples points for attraction searches

**GPX Export:**
- Full route geometry (2000+ coordinate points)
- Accurate road-following paths
- Compatible with OsmAnd, Organic Maps, Maps.me
- Both route (`<rte>`) and track (`<trk>`) elements

## Services Used

### 1. Google Places API (New)

**Purpose:** Primary data source for all attractions, hotels, restaurants, and vets

**Data Provided:**
- Business names and addresses
- Ratings and review counts
- Phone numbers and websites
- Opening hours and 24/7 status
- Place IDs for deduplication
- Geographic coordinates

**API Limits:**
- Free tier: $200/month credit
- Typical trip cost: $2-5
- Billing required but generous limits

### 2. OpenStreetMap Nominatim

**Purpose:** Geocoding and reverse geocoding

**Data Provided:**
- City coordinates from names
- State boundaries
- Address details
- Reverse geocoding (coordinates → city names)

**Rate Limits:**
- 1 request per second
- Cached to avoid repeated queries
- Public service (free)

### 3. OSRM (Open Source Routing Machine)

**Purpose:** Road routing and geometry

**Data Provided:**
- Actual road routes between cities
- Driving distances and times
- Route geometry (coordinate points)
- Turn-by-turn waypoints

**Service:**
- Public API: http://router.project-osrm.org
- Free to use
- Based on OpenStreetMap data

### 4. Wikipedia API

**Purpose:** Educational content for attractions

**Data Provided:**
- Article summaries
- Full article links
- Educational context for parks, museums, monuments

**Usage:**
- Automatic for national parks
- Automatic for museums
- Links in map popups and summaries

### 5. Wikivoyage API

**Purpose:** Travel guides for cities

**Data Provided:**
- City travel guides
- Tourist information
- Practical tips for visitors

**Usage:**
- Automatic for all stop cities
- Links in waypoints and summaries

### 6. Folium

**Purpose:** Interactive map generation

**Features:**
- LayerControl for toggling categories
- Custom markers for each attraction type
- Popups with detailed information
- Distance markers between stops
- Fullscreen and measure tools

---

**Back to:** [README.md](README.md) | [GPX Import Guide](GPX_IMPORT_GUIDE.md) | [Documentation](#documentation)
