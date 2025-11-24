#!/bin/bash
# Build script for PyInstaller executable

set -e  # Exit on error

echo "🔨 Building executable with PyInstaller..."
echo "========================================"

# Activate virtual environment
source venv/bin/activate

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.spec

# Build the executable
echo "📦 Building executable..."
pyinstaller --name="RoadTripPlanner" \
    --onefile \
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
    gui_app.py

echo ""
echo "✅ Build complete!"
echo "📁 Executable location: dist/RoadTripPlanner"
echo ""
echo "To run: ./dist/RoadTripPlanner"
echo "To distribute: Share the dist/RoadTripPlanner file"
echo ""
echo "Note: Users will need to create their own .env file with API key"
