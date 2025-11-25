# Road Trip Planner Icons

This directory is reserved for future application icons.

## Future Icon Files

When native installers are created, these icon files may be needed:
- `icon.icns` - macOS icon (512x512 or larger)
- `icon.ico` - Windows icon (256x256 with multiple sizes)
- `icon.png` - Linux icon (512x512 recommended)
- `splash.png` - Splash screen (1024x1024 or larger)

## Creating Icons

You can use online tools or these commands:

**From PNG to ICO (Windows):**
```bash
convert icon.png -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico
```

**From PNG to ICNS (macOS):**
```bash
mkdir icon.iconset
sips -z 16 16 icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32 icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32 icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64 icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256 icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512 icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
iconutil -c icns icon.iconset
```

## Placeholder

Currently, the GUI uses the default PyQt6 window icon. Custom icons can be added here for future packaging with PyInstaller.

Icon should represent:
- 🚗 Car/road trip theme
- 🐾 Pet-friendly aspect
- 🗺️ Map/navigation element
