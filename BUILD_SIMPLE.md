# Simple Build Guide

Quick guide to building checkm8 packages.

## Prerequisites

1. **Python 3.8+** with pip installed

   **macOS users**: Ensure Python has tkinter support:
   ```bash
   # Using Homebrew Python (recommended)
   brew install python@3.11 python-tk@3.11

   # Verify tkinter works
   python3 -c "import tkinter; print('tkinter OK')"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Build Steps

### 1. Generate Icons (First Time Only)

```bash
python assets/generate_icon.py
```

**On macOS only**, create the `.icns` icon:
```bash
cd assets
mkdir -p icon.iconset
sips -z 16 16     icon_256.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon_256.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon_256.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon_256.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon_256.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon_256.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon_256.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon_256.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon_256.png --out icon.iconset/icon_512x512.png
iconutil -c icns icon.iconset -o icon.icns
cd ..
```

### 2. Build the Application

```bash
python -m PyInstaller checkm8.spec --clean
```

This creates the application in `dist/`:

- **Windows**: `dist/checkm8/checkm8.exe`
- **macOS**: `dist/checkm8.app`
- **Linux**: `dist/checkm8/checkm8`

### 3. Create Distribution Package

#### Windows
```powershell
cd dist
Compress-Archive -Path checkm8 -DestinationPath checkm8-windows-portable.zip
```

#### macOS
```bash
hdiutil create -volname "checkm8" -srcfolder dist/checkm8.app -ov -format UDZO dist/checkm8-macos.dmg
```

#### Linux
```bash
cd dist
tar -czf checkm8-linux-x86_64.tar.gz checkm8/
```

## Quick Build (Alternative)

Use the build script:
```bash
python build.py
```

This automatically:
1. Builds with PyInstaller
2. Creates the distribution package for your platform

## Outputs

### Windows
- `checkm8-windows-portable.zip` - Extract and run `checkm8.exe`

### macOS
- `checkm8-macos.dmg` - Open and drag to Applications

### Linux
- `checkm8-linux-x86_64.tar.gz` - Extract and run `./checkm8/checkm8`

## Testing

### Windows
```bash
dist\checkm8\checkm8.exe
```

### macOS
```bash
open dist/checkm8.app
```

### Linux
```bash
dist/checkm8/checkm8
```

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --force-reinstall
```

### macOS: "checkm8.app is damaged"
```bash
xattr -cr dist/checkm8.app
```

### Linux: Permission denied
```bash
chmod +x dist/checkm8/checkm8
```

## Clean Build

```bash
python build.py --clean
# Then rebuild
python build.py
```
