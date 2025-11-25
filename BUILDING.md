# Building the Road Trip Planner Executable

> **Back to main README:** [README.md](README.md)  
> **GUI Details:** [GUI_IMPLEMENTATION.md](GUI_IMPLEMENTATION.md)

This document explains how to build a standalone executable using PyInstaller.

## Overview

PyInstaller creates a single-file executable that bundles:
- Python runtime
- PyQt6 and all dependencies
- Your application code
- Required data files

The result is a ~271MB executable (Linux) or ~464MB .app bundle (macOS) that users can run without installing Python.

## Prerequisites

- Python 3.11+ with virtual environment
- All project dependencies installed (`pip install -r requirements.txt`)
- PyInstaller installed (`pip install pyinstaller`)

## Building on Linux

### Quick Build

```bash
source venv/bin/activate
./build_pyinstaller.sh
```

The script will:
1. Clean previous builds
2. Bundle all dependencies
3. Create executable at `dist/RoadTripPlanner`

### Build Time

- **First build**: 5-10 minutes (compiles everything)
- **Subsequent builds**: 2-3 minutes (reuses cache)

### Output

```
dist/
└── RoadTripPlanner    # Single executable file (~163MB)
```

## Manual Build

If you need custom build options:

```bash
source venv/bin/activate

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
```

## Testing the Executable

```bash
# Make sure it's executable
chmod +x dist/RoadTripPlanner

# Run it
./dist/RoadTripPlanner
```

**Important**: Create a `.env` file in the same directory as the executable with your API key:

```bash
echo "GOOGLE_PLACES_API_KEY=your_key_here" > dist/.env
```

## Distribution

### GitHub Releases (Recommended)

1. Tag your release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. Create GitHub Release:
   - Go to repository → Releases → Draft New Release
   - Upload `dist/RoadTripPlanner`
   - Add release notes

3. Users download and run:
   ```bash
   chmod +x RoadTripPlanner
   ./RoadTripPlanner
   ```

### Direct Distribution

If sharing directly:

1. Create checksum for verification:
   ```bash
   sha256sum RoadTripPlanner > RoadTripPlanner.sha256
   ```

2. Share both files:
   - `RoadTripPlanner` (executable)
   - `RoadTripPlanner.sha256` (checksum)

3. Users verify:
   ```bash
   sha256sum -c RoadTripPlanner.sha256
   ```

## Platform Support

## Platform Support

### Linux (x86-64)

Build a single-file executable:

```bash
source venv/bin/activate
./build_pyinstaller.sh
# Creates: dist/RoadTripPlanner (~271MB)
```

### macOS (Universal2)

Build a .app bundle:

```bash
source venv/bin/activate
./build_pyinstaller_macos.sh
# Creates: dist/RoadTripPlanner.app (~464MB)
```

The macOS build uses `--onedir --windowed` to create a proper .app bundle. Settings and trip routes are automatically saved to `~/Documents/RoadTripPlanner/` when running as a bundled app.

### Windows

Windows builds are not yet available. To build for Windows:

```cmd
REM On Windows:
venv\Scripts\activate.bat
pyinstaller --name="RoadTripPlanner" --onefile --windowed gui_app.py
REM Creates: dist\RoadTripPlanner.exe
```

> **Note:** PyInstaller executables are platform-specific. You must build on the target OS.

## Troubleshooting

### "ImportError: No module named..."

Add the missing module to `--hidden-import` in the build script.

### "File not found" errors

Use `--add-data` to include data files:
```bash
--add-data="myfile.txt:."
```

### Executable too large

Current size (~163MB) is normal because it includes:
- Python runtime (~50MB)
- PyQt6 (~80MB)
- Dependencies (~30MB)

To reduce size, consider:
- Using `--exclude-module` for unused packages
- Compressing with UPX (not recommended for PyQt6)

### Application won't start

1. Run from terminal to see error messages:
   ```bash
   ./dist/RoadTripPlanner
   ```

2. Check for missing `.env` file with API key

3. Verify PyQt6 libraries are bundled:
   ```bash
   ldd dist/RoadTripPlanner | grep -i qt
   ```

## Clean Build

Remove all build artifacts:

```bash
rm -rf build/ dist/ *.spec
```

Then rebuild from scratch.

## Advanced Options

### Debug Build

For debugging, create a non-windowed build that shows console output:

```bash
pyinstaller --name="RoadTripPlannerDebug" \
    --onefile \
    --console \
    gui_app.py
```

### One-Directory Build

For faster startup (but multiple files):

```bash
pyinstaller --name="RoadTripPlanner" \
    --onedir \
    --windowed \
    gui_app.py
```

Creates `dist/RoadTripPlanner/` directory with executable and dependencies.

## Build Automation

### GitHub Actions (Future)

Example workflow for automated builds:

```yaml
name: Build Executable
on: [push, release]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: ./build_pyinstaller.sh
      - uses: actions/upload-artifact@v3
        with:
          name: RoadTripPlanner-linux
          path: dist/RoadTripPlanner
```

## Why PyInstaller?

**Advantages:**
- ✅ Simple to use
- ✅ Works on Linux, macOS, Windows
- ✅ Single-file executables
- ✅ No external dependencies for users
- ✅ Good PyQt6 support

**Alternatives:**
- **cx_Freeze**: Cross-platform freezing - similar to PyInstaller
- **Nuitka**: Python-to-C compiler - faster but larger builds
- **py2app** (macOS only): Alternative macOS bundler

PyInstaller was chosen for simplicity and reliability with PyQt6 across all platforms.

## Support

For PyInstaller issues:
- Docs: https://pyinstaller.org/
- GitHub: https://github.com/pyinstaller/pyinstaller
- FAQ: https://pyinstaller.org/en/stable/FAQ.html

For application issues:
- Open issue on GitHub: https://github.com/KM4HQZ/road-trip-planner/issues

---

**Ready to build!** Run `./build_pyinstaller.sh` to create your executable. 🚀
