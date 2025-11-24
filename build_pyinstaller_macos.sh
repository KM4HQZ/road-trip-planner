#!/bin/bash
# Build script for PyInstaller executable on macOS

set -e  # Exit on error

# Fix PATH for macOS
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

echo "🔨 Building macOS executable with PyInstaller..."
echo "========================================"

# Activate virtual environment
source venv/bin/activate

# Clean previous builds
echo "🧹 Cleaning previous builds..."
/bin/rm -rf dist/ build/ *.spec

# Build the executable for macOS
echo "📦 Building macOS executable..."
pyinstaller --name="RoadTripPlanner" \
    --onedir \
    --windowed \
    --add-data="config.py:." \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=PyQt6.QtWebEngineWidgets \
    --hidden-import=folium \
    --hidden-import=geopy \
    --hidden-import=requests \
    --hidden-import=bs4 \
    --hidden-import=markdown \
    --hidden-import=pandas \
    --hidden-import=tabulate \
    --hidden-import=dotenv \
    --collect-all PyQt6 \
    --collect-all folium \
    --osx-bundle-identifier=com.km4hqz.roadtripplanner \
    gui_app.py

echo ""
echo "✅ Build complete!"
echo "📁 Application bundle: dist/RoadTripPlanner.app"
echo ""
echo "To run: open dist/RoadTripPlanner.app"
echo "To distribute: Share the dist/RoadTripPlanner.app bundle (zip it first)"
echo ""
echo "Note: Users will need to create their own .env file with API key"
