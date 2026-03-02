# Build Fixes Applied

## Issues Fixed

### 1. macOS: `ModuleNotFoundError: No module named '_tkinter'`

**Problem**: PyInstaller wasn't properly bundling tkinter and its dependencies on macOS.

**Fixes**:
- Updated `checkm8.spec` to explicitly include:
  - `_tkinter` and all tkinter submodules
  - PIL image handling modules
  - CustomTkinter assets directory
- Added system dependency installation in GitHub Actions workflow to ensure `python-tk` is available
- Added tkinter verification step in build process

**Files changed**:
- `checkm8.spec` - Added comprehensive hiddenimports for tkinter
- `.github/workflows/build-release.yml` - Added `brew install python-tk@3.11`
- `BUILD_SIMPLE.md` - Added macOS prerequisites

### 2. Simplified Build Process

**Problem**: Build process was too complex with multiple installer types that weren't needed.

**Fixes**:
- Removed Windows `.exe` installer (Inno Setup) - now just portable ZIP
- Removed macOS `.pkg` installer - now just `.dmg`
- Removed Linux `.deb` package - now just tarball
- Simplified to one distributable per platform

**Benefits**:
- Faster builds
- More reliable (fewer dependencies)
- Easier to distribute
- Works on all systems without installation

**Files changed**:
- `build.py` - Replaced complex installer functions with simple archive creation
- `.github/workflows/build-release.yml` - Removed installer build steps
- `PUBLISH.md` - Updated to reflect simpler packages

### 3. Missing `.icns` Icon on macOS

**Problem**: The `.icns` file wasn't being created, causing PyInstaller to fail or produce unbranded apps.

**Fixes**:
- Made icon optional in `checkm8.spec` (checks if file exists before using)
- GitHub Actions workflow now creates all required icon sizes for .icns
- Added fallback to build without icon if creation fails

**Files changed**:
- `checkm8.spec` - Added `Path().exists()` checks before using icon
- `.github/workflows/build-release.yml` - Improved icon generation script

### 4. DMG Creation Reliability

**Problem**: `create-dmg` tool is finicky and often fails in GitHub Actions.

**Fixes**:
- Replaced `create-dmg` with simple `hdiutil` command
- Always uses `hdiutil` for consistency
- No fancy DMG features, just a simple disk image

**Files changed**:
- `.github/workflows/build-release.yml` - Replaced create-dmg with hdiutil
- `build.py` - Added `build_macos_dmg()` using hdiutil

### 5. Release Notes and Documentation

**Problem**: Release notes mentioned installers that don't exist anymore.

**Fixes**:
- Updated release notes template to only mention portable packages
- Clarified installation instructions for each platform
- Added macOS Gatekeeper bypass instructions

**Files changed**:
- `.github/workflows/build-release.yml` - Updated release notes template
- `PUBLISH.md` - Updated package list
- `BUILD_SIMPLE.md` - Created simpler build guide

### 6. Hardcoded Version Numbers

**Problem**: Version numbers were hardcoded in multiple places.

**Status**: Not fully fixed yet, but simplified by reducing number of build artifacts. Future improvement: extract version from `config/constants.py`.

## Build Results

After these fixes, the build produces:

### Windows
- `checkm8-windows-portable.zip` (one file, extract and run)

### macOS
- `checkm8-macos.dmg` (one file, drag to Applications)

### Linux
- `checkm8-linux-x86_64.tar.gz` (one file, extract and run)

## Testing Locally

### macOS
```bash
# 1. Ensure tkinter is available
brew install python@3.11 python-tk@3.11
python3 -c "import tkinter; print('OK')"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate icons
python assets/generate_icon.py
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

# 4. Build
python -m PyInstaller checkm8.spec --clean

# 5. Test
open dist/checkm8.app

# 6. Create DMG
hdiutil create -volname "checkm8" -srcfolder dist/checkm8.app -ov -format UDZO dist/checkm8-macos.dmg
```

### Windows
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate icons
python assets/generate_icon.py

# 3. Build
python -m PyInstaller checkm8.spec --clean

# 4. Test
dist\checkm8\checkm8.exe

# 5. Create ZIP
cd dist
Compress-Archive -Path checkm8 -DestinationPath checkm8-windows-portable.zip
```

### Linux
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate icons
python assets/generate_icon.py

# 3. Build
python -m PyInstaller checkm8.spec --clean

# 4. Test
dist/checkm8/checkm8

# 5. Create tarball
cd dist
tar -czf checkm8-linux-x86_64.tar.gz checkm8/
```

## GitHub Actions

The automated build should now work reliably. To trigger:

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

Or use the helper script:
```powershell
.\release.ps1 1.0.0 "Initial release"
```

Monitor the build at:
`https://github.com/YOUR_USERNAME/checkm8-jailbreak/actions`

## Known Limitations

1. **macOS Code Signing**: App is not code-signed, users will need to right-click → Open the first time
2. **Windows SmartScreen**: Unsigned .exe may trigger warnings
3. **Version Numbers**: Still hardcoded in some places (future improvement)
4. **Icon Quality**: Generated programmatically, could be improved with a professional design

## Next Steps

If builds still fail:
1. Check GitHub Actions logs for specific errors
2. Test locally on the failing platform first
3. Verify all dependencies are in `requirements.txt`
4. Ensure icons were generated correctly
