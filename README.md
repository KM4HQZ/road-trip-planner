# Dynamic Pet-Friendly Road Trip Planner 🚗🐾

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

An intelligent road trip planning tool that automatically finds pet-friendly hotels, emergency vets, parks, restaurants, and attractions for multi-city road trips. **Available as both a GUI application and command-line tool!**

> **Quick Links:**
> - 🗺️ [View Live Example Trip](https://km4hqz.github.io/road-trip-planner/) - Atlanta → Colorado Springs → Las Vegas → Los Angeles → Atlanta
> - 📱 [GPX Import Guide](GPX_IMPORT_GUIDE.md) - Use your trip on iPhone or Android with OsmAnd
> - 📱 [Pixel Quick Start](PIXEL_QUICK_START.md) - Fast setup for Google Pixel users
> - 🎯 [Feature Details](FEATURES.md) - Search algorithms, scoring systems, and technical details

## 📑 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Output Files](#-output-files)
- [Troubleshooting](#️-troubleshooting)
- [Documentation](#-documentation)
- [License](#-license)

## ✨ Features

### What It Finds
- 🏨 **Pet-friendly hotels** at strategic stops (La Quinta, Drury Inn, Red Roof, Best Western, Kimpton, and more)
- 🏥 **24/7 emergency vets** with strict verification (confirmed hours, prioritized in results)
- 🏞️ **National parks** in every state you pass through (4.3+ stars, 1000+ reviews)
- 🗿 **Monuments & memorials** along your route (state-by-state searches)
- 🌲 **Parks** for exercise breaks (sampled every 75 miles + top picks at cities)
- 🏛️ **Museums** and cultural attractions at stop cities (top 3 per city)
- 🍽️ **Dog-friendly restaurants** with outdoor seating (explicit pet-friendly search)
- 🐾 **Dog parks** for off-leash play (top 2 per city)
- 📸 **Scenic viewpoints** along the way (overlooks, vista points)
- ⚡ **EV charging stations** every 15 miles (all networks: Electrify America, ChargePoint, EVgo, Tesla)

### Smart Planning
- **City-based stops**: Finds actual cities ~250 miles apart, not random coordinates
- **Multi-city routes**: Add unlimited waypoints with `--via` for varied return trips
- **Actual road routes**: Uses OSRM for accurate distances and driving times
- **Smart filtering**: High-rated attractions only (4.0-4.5+ stars depending on category)
- **Deduplication**: Automatically removes duplicate results
- **Wikipedia integration**: Educational content for parks, museums, and monuments
- **Wikivoyage guides**: Travel information for every stop city

### Output Options
- 🗺️ **Interactive HTML map** with toggleable layers and detailed popups
- 📱 **GPX file** for OsmAnd, Organic Maps, Maps.me navigation (2000+ route points)
- 📄 **Markdown summary** with all details in human-readable format
- 📊 **JSON data file** with complete structured trip information
- 🖥️ **GUI application** with embedded maps and one-click exports
- ⌨️ **Command-line tool** for automation and scripting

> **See [FEATURES.md](FEATURES.md) for detailed information about search algorithms, scoring systems, and verification processes.**

## 📥 Installation

### Option A: From Source (Recommended for Development)

```bash
git clone https://github.com/KM4HQZ/road-trip-planner.git
cd road-trip-planner
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Option B: Linux Executable

Download the pre-built executable (no Python installation required):

1. **Download:** [RoadTripPlanner v1.1.1](https://github.com/KM4HQZ/road-trip-planner/releases/download/v1.1.1/RoadTripPlanner-v1.1.1-Linux-x86_64) (272MB)
2. **Make executable:** `chmod +x RoadTripPlanner-v1.1.1-Linux-x86_64`
3. **Run:** `./RoadTripPlanner-v1.1.1-Linux-x86_64`
4. **Configure:** Create a `.env` file in the same directory with your API key

### Option C: macOS Application

Download the native .app bundle (no Python installation required):

1. **Download:** [RoadTripPlanner-macOS-v1.0.0.zip](https://github.com/KM4HQZ/road-trip-planner/releases/download/v1.0.0/RoadTripPlanner-macOS-v1.0.0.zip) (464MB)
2. **Unzip:** `unzip RoadTripPlanner-macOS-v1.0.0.zip`
3. **Open:** Double-click `RoadTripPlanner.app`
4. **Settings:** Saved to `~/Documents/RoadTripPlanner/`

> **Building from source:** See [BUILDING.md](BUILDING.md) for instructions on building your own executables with PyInstaller.

## 🚀 Quick Start

### 1. Set Up Google Places API

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

## 🚀 Usage

### GUI Application (Easiest)

```bash
source venv/bin/activate  # If installed from source
python gui_app.py
# Or use: ./launch_gui.sh
```

**Features:**
- Easy form interface with all options
- Real-time progress updates
- Embedded map viewer
- One-click export buttons
- Settings dialog for API configuration

### Command Line

**Basic trip:**
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL"
```

**Multi-city route (recommended over round-trip):**
```bash
python plan_trip.py "Atlanta, GA" "Seattle, WA" --via "Denver, CO" --via "Portland, OR"
```

**Customize options:**
```bash
# Shorter stops (6 hours driving instead of 8)
python plan_trip.py "Atlanta, GA" "Denver, CO" --target-hours 6

# Skip specific categories
python plan_trip.py "Atlanta, GA" "Denver, CO" --no-museums --no-restaurants

# Only generate GPX (no map, summary, or data files)
python plan_trip.py "Atlanta, GA" "Denver, CO" --no-map --no-summary --no-data
```

**Available flags:**
- **Search toggles:** `--no-hotels`, `--all-hotels`, `--no-vets`, `--no-national-parks`, `--no-monuments`, `--no-parks`, `--no-museums`, `--no-restaurants`, `--no-dog-parks`, `--no-viewpoints`, `--no-ev-chargers`
- **Export toggles:** `--no-gpx`, `--no-map`, `--no-summary`, `--no-data`
- **Route options:** `--via "City, State"` (multiple allowed), `--target-hours N`, `--roundtrip`

## �️ GUI Usage

### Launching the GUI

```bash
source venv/bin/activate
python gui_app.py
```

### GUI Features

1. **Plan Trip Tab**
   - Enter origin and destination cities
   - Add optional via cities for varied routes
   - Configure stop distance and waypoint interval
   - **Search Options**: Toggle each attraction category (hotels, vets, parks, museums, restaurants, dog parks, viewpoints, EV chargers, national parks, monuments)
   - **Pet-Friendly Toggle**: Search all hotels or just pet-friendly chains
   - **Export Options**: Choose which files to generate (map, GPX, summary, data)
   - Real-time progress dialog during planning

2. **Results Tab**
   - View your trip map embedded in the application
   - See trip summary (distance, time, stops)
   - Read detailed trip information
   - Export GPX, summary, or data files

3. **Settings Menu**
   - Configure Google Places API key
   - Manage application preferences
   - Clear location cache

4. **Export Options**
   - Open map in default browser
   - Export GPX for navigation apps
   - Export summary markdown
   - Export trip data JSON

## �📋 Command Line Usage Examples

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
python plan_trip.py "Atlanta, GA" "Chicago, IL" --target-hours 6
# Stops every ~6 hours of driving instead of default 8
```

### Old-Style Round Trip (Not Recommended)
```bash
python plan_trip.py "Atlanta, GA" "Chicago, IL" --roundtrip
# Takes same route back - use --via instead for variety!
```

### Customize What to Search
```bash
# Skip specific categories
python plan_trip.py "Atlanta, GA" "Denver, CO" --no-museums --no-restaurants

# Search all hotels (not just pet-friendly)
python plan_trip.py "Atlanta, GA" "Denver, CO" --all-hotels

# Minimal trip (just route and hotels)
python plan_trip.py "Atlanta, GA" "Denver, CO" --no-vets --no-parks --no-museums --no-restaurants --no-dog-parks --no-viewpoints --no-ev-chargers --no-national-parks --no-monuments
```

### Customize Export Options
```bash
# Only generate the map (no GPX, summary, or data files)
python plan_trip.py "Atlanta, GA" "Denver, CO" --no-gpx --no-summary --no-data

# Only generate GPX and summary (no map or data)
python plan_trip.py "Atlanta, GA" "Denver, CO" --no-map --no-data
```

**Available Toggles:**
- Search: `--no-hotels`, `--all-hotels`, `--no-vets`, `--no-national-parks`, `--no-monuments`, `--no-parks`, `--no-museums`, `--no-restaurants`, `--no-dog-parks`, `--no-viewpoints`, `--no-ev-chargers`
- Export: `--no-gpx`, `--no-map`, `--no-summary`, `--no-data`

## 📂 Output Files

Each trip generates up to four files in the `trip routes/` directory (customize with export toggles):

### 1. Interactive Map (HTML)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN.html`

- Blue route line following actual highways with distance markers
- Toggleable layers for each category (hotels, vets, parks, museums, etc.)
- "Toggle All" button to show/hide all layers at once
- Rich popups with ratings, contact info, and links
- Fullscreen mode and measure tool

### 2. GPX Navigation File
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN.gpx`

- Complete driving route with 2000+ coordinate points (actual roads, not straight lines)
- All stop cities, hotels, vets, and attractions as waypoints
- Import into OsmAnd, Organic Maps, Maps.me, or most GPS devices
- **See [GPX Import Guide](GPX_IMPORT_GUIDE.md) for iOS and Android transfer instructions**

### 3. Trip Summary (Markdown)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_summary.md`

Human-readable report with trip overview, hotel recommendations, vet locations, and categorized attractions with ratings.

### 4. Complete Data (JSON)
`trip_Atlanta_GA_Chicago_IL_via_Nashville_TN_data.json`

Structured data for all stops, hotels, vets, and attractions. Useful for automation or custom processing.

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

### How sessions work

Road Trip Planner does **not** use autonomous agents or long-lived "agent sessions." Each run is independent:

- **CLI:** Every `python plan_trip.py ...` command starts a fresh planning run and exits when it finishes.
- **GUI planning:** Clicking **Plan Trip** starts a new background planning job for the current window.
- **What persists:** Your Google Places API key is saved to `.env`, some GUI preferences are stored with `QSettings`, and geocoding results stay in `location_cache.json` until you clear the cache.
- **Trip results:** Generated trip data stays in memory only for the current GUI window unless you save/export the files. You can reopen a saved JSON trip later with **File → Open Trip Data...**.

So if you close the app or start a new command, the planner does not resume a previous run automatically—it starts from scratch unless you reload exported trip data.

### Missing dependencies

If you see import errors, make sure the virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install --upgrade requests beautifulsoup4 markdown geopy folium pandas tabulate python-dotenv
```

## � Documentation

## 📚 Documentation

### User Guides
- **[GPX Import Guide](GPX_IMPORT_GUIDE.md)** - Transfer GPX files to iPhone or Android with OsmAnd, Organic Maps, or Maps.me
- **[Pixel Quick Start](PIXEL_QUICK_START.md)** - Fast setup guide for Google Pixel users
- **[Feature Details](FEATURES.md)** - Complete technical details: search algorithms, scoring formulas, and verification processes
- **[Workflow Diagram](WORKFLOW_DIAGRAM.md)** - Visual overview of the planning → navigation workflow

### Developer Documentation
- **[Building Executables](BUILDING.md)** - Build standalone executables with PyInstaller for Linux and macOS
- **[GUI Implementation](GUI_IMPLEMENTATION.md)** - PyQt6 GUI architecture and design details
- **[GPX Feature Summary](GPX_FEATURE_SUMMARY.md)** - Technical details of GPX export implementation

### API Documentation
All core modules are documented with docstrings:
- `services/` - External API integrations (Google Places, Nominatim, OSRM, Wikipedia)
- `models/` - Data models (Hotel, Veterinarian, Attraction, Location)
- `utils/` - Helper functions (distance calculations, map generation, GPX export)
- `gui/` - PyQt6 GUI components (main window, map viewer, dialogs)

## �📄 License

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
