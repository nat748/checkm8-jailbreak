# Building checkm8 Distributables

This guide explains how to build distributable packages for Windows, macOS, and Linux.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Build for current platform
python build.py

# Clean build artifacts
python build.py --clean
```

## Prerequisites

### All Platforms

- Python 3.8 or newer
- pip (Python package manager)
- All dependencies from `requirements.txt`

### Windows (.exe + installer)

- **PyInstaller** (installed via requirements.txt)
- **Inno Setup 6** (optional, for creating `.exe` installer)
  - Download from: https://jrsoftware.org/isdl.php
  - Used to create `checkm8-1.0.0-setup.exe`

### macOS (.app + .pkg)

- **PyInstaller** (installed via requirements.txt)
- **Xcode Command Line Tools** (for `pkgbuild`)
  ```bash
  xcode-select --install
  ```
- **iconutil** (comes with Xcode, for creating `.icns` icon)

### Linux (.deb)

- **PyInstaller** (installed via requirements.txt)
- **dpkg-deb** (usually pre-installed on Debian/Ubuntu)
  ```bash
  sudo apt-get install dpkg-dev
  ```

## Step-by-Step Build Instructions

### 1. Generate Application Icon

```bash
python assets/generate_icon.py
```

This creates:
- `assets/icon.ico` (Windows)
- `assets/icon.png` (Linux)
- `assets/icon_256.png` (for macOS conversion)

**On macOS only**, create the `.icns` file:
```bash
cd assets
mkdir icon.iconset
sips -z 16 16   icon_256.png --out icon.iconset/icon_16x16.png
sips -z 32 32   icon_256.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32   icon_256.png --out icon.iconset/icon_32x32.png
sips -z 64 64   icon_256.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon_256.png --out icon.iconset/icon_128x128.png
sips -z 256 256 icon_256.png --out icon.iconset/icon_128x128@2x.png
iconutil -c icns icon.iconset -o icon.icns
cd ..
```

### 2. Build the Application

#### Windows

```bash
python build.py
```

**Output:**
- `dist/checkm8/checkm8.exe` - Standalone executable
- `dist/checkm8-1.0.0-setup.exe` - Installer (if Inno Setup installed)

**Distribution:**
- Option 1: Distribute the entire `dist/checkm8` folder as a portable app
- Option 2: Distribute `checkm8-1.0.0-setup.exe` as an installer

**Testing:**
```bash
# Run the standalone exe
dist\checkm8\checkm8.exe

# Or install via the setup wizard
dist\checkm8-1.0.0-setup.exe
```

#### macOS

```bash
python build.py
```

**Output:**
- `dist/checkm8.app` - Application bundle
- `dist/checkm8-1.0.0.pkg` - Installer package

**Distribution:**
- Option 1: Distribute `checkm8.app` (drag-and-drop to Applications)
- Option 2: Distribute `checkm8-1.0.0.pkg` (double-click installer)

**Testing:**
```bash
# Run the app
open dist/checkm8.app

# Or install the pkg
open dist/checkm8-1.0.0.pkg
```

**Code Signing (optional but recommended):**
```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/checkm8.app

# Notarize with Apple (requires developer account)
xcrun notarytool submit dist/checkm8-1.0.0.pkg --apple-id your@email.com --password app-specific-password --team-id TEAMID
```

#### Linux (Debian/Ubuntu)

```bash
python build.py
```

**Output:**
- `dist/checkm8/checkm8` - Standalone binary
- `dist/checkm8_1.0.0_amd64.deb` - Debian package

**Distribution:**
- Option 1: Distribute the binary folder `dist/checkm8`
- Option 2: Distribute `checkm8_1.0.0_amd64.deb`

**Testing:**
```bash
# Run the standalone binary
./dist/checkm8/checkm8

# Or install the .deb
sudo dpkg -i dist/checkm8_1.0.0_amd64.deb
checkm8
```

## Build Output Structure

```
dist/
├── checkm8/                    # Portable folder (Windows/Linux)
│   ├── checkm8.exe             # Windows executable
│   ├── checkm8                 # Linux binary
│   └── _internal/              # Dependencies and resources
├── checkm8.app/                # macOS app bundle
├── checkm8-1.0.0-setup.exe     # Windows installer
├── checkm8-1.0.0.pkg           # macOS installer
└── checkm8_1.0.0_amd64.deb     # Debian package
```

## Troubleshooting

### "PyInstaller command not found"

```bash
pip install --upgrade pyinstaller
```

### Windows: "Unable to find icon.ico"

Make sure you ran `python assets/generate_icon.py` first.

### macOS: ".icns file not found"

You need to manually create the `.icns` using the commands in step 1, or skip it by removing the `icon=` parameter from `checkm8.spec`.

### Linux: "dpkg-deb: command not found"

```bash
sudo apt-get install dpkg-dev
```

### "Import Error" when running built executable

This usually means a hidden import is missing. Add it to `hiddenimports` in `checkm8.spec`:

```python
hiddenimports=[
    'your.missing.module',
],
```

Then rebuild with `python build.py --clean && python build.py`.

### Large executable size

PyInstaller bundles the Python interpreter and all dependencies. To reduce size:

1. Remove unused imports from your code
2. Add exclusions to `checkm8.spec`:
   ```python
   excludes=['matplotlib', 'numpy', 'pandas'],
   ```
3. Use UPX compression (enabled by default)

## Distribution Checklist

Before distributing, ensure:

- [ ] Version number updated in:
  - `config/constants.py` (APP_VERSION)
  - `checkm8.spec` (version in info_plist for macOS)
  - `build.py` (version strings)
  - `installer_windows.iss` (MyAppVersion)
- [ ] Tested on clean machine without Python installed
- [ ] Icon displays correctly
- [ ] All features work (USB detection, emulator, setup wizard)
- [ ] About window shows correct credits
- [ ] LICENSE file included
- [ ] CLAUDE.md included (bundled in app)

## Automated CI/CD

For automated builds on GitHub Actions or similar:

```yaml
# Example .github/workflows/build.yml
name: Build Packages

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build.py
      - uses: actions/upload-artifact@v3
        with:
          name: windows-build
          path: dist/*.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build.py
      - uses: actions/upload-artifact@v3
        with:
          name: macos-build
          path: dist/*.pkg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python build.py
      - uses: actions/upload-artifact@v3
        with:
          name: linux-build
          path: dist/*.deb
```

## License & Credits

This build system creates packages for the checkm8 GUI tool. See the About window in the app for full credits of all included open-source components.
