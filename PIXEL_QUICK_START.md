# 📱 Quick Start: GPX on Your Google Pixel

> **Need more detail?** See the full [GPX Import Guide](GPX_IMPORT_GUIDE.md) for comprehensive instructions.  
> **Back to main README:** [README.md](README.md)

## Fastest Method for Your Pixel

### Step 1: Install OsmAnd
```
Play Store → Search "OsmAnd" → Install
```
Free, offline capable, excellent GPX support!

### Step 2: Run Your Trip Planner
```bash
cd road-trip-planner
source venv/bin/activate
python plan_trip.py "Start City, ST" "End City, ST"
```

Or use the GUI:
```bash
python gui_app.py
```

### Step 3: Find Your GPX File
Look in `trip routes/` folder:
```
trip_Start_City_ST_End_City_ST.gpx
```

### Step 4: Transfer to Pixel
**Easiest methods:**

**Method A: Email**
1. Email the `.gpx` file to yourself
2. Open email on Pixel
3. Tap the attachment
4. Select "Open with OsmAnd"
5. ✅ Done!

**Method B: Google Drive**
1. Upload `.gpx` to Google Drive from computer
2. Open Drive app on Pixel
3. Tap the file → "Open with OsmAnd"
4. ✅ Done!

**Method C: Direct Import to OsmAnd**
1. Transfer `.gpx` to: `/Android/data/net.osmand/files/tracks/`
2. In OsmAnd: Menu → My Places → Tracks
3. Tap your file → "Show on map"
4. ✅ Done!

### Step 5: Use in OsmAnd
1. Route appears on map automatically
2. Tap any waypoint to see details
3. Tap "Navigate" to start turn-by-turn
4. Hotels, vets, and attractions are all marked!

## What You'll See

- 📍 **Blue dots**: Your major stop cities
- 🏨 **Hotel icons**: Pet-friendly accommodations
- 🏥 **Medical icons**: 24/7 emergency vets
- 🌲 **Park icons**: Scenic stops and attractions
- 🍽️ **Restaurant icons**: Dog-friendly dining
- 🐾 **Paw icons**: Dog parks for exercise
- 📸 **Camera icons**: Scenic viewpoints

## Pro Tips

1. **Download offline maps** in OsmAnd for your route before leaving
2. **Tap waypoints** to see ratings, phone numbers, addresses
3. **Configure map layers** if you want to show/hide certain POI types
4. **Keep phone charged** - navigation uses battery!

## Alternative Apps (Also Great)

- **Organic Maps**: Lighter weight, faster
- **Maps.me**: Popular with good offline support
- **Organic Maps**: Fastest, most lightweight
- **Maps.me**: Popular, easy to use

All work the same way - just "Open with..." the app you prefer!

---

**Questions?** See full guide: `GPX_IMPORT_GUIDE.md`
