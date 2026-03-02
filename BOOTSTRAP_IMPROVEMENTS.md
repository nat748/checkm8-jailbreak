# Bootstrap Installer Improvements

## Overview

The bootstrap installer has been enhanced to support multiple package managers and provide better user choice. Users can now select between **Sileo**, **Zebra**, or **Cydia** when installing the jailbreak bootstrap.

## What Changed

### 1. Package Manager Selection Dialog

Created a new dialog ([gui/package_manager_dialog.py](gui/package_manager_dialog.py)) that lets users choose their preferred package manager before installation:

- **Sileo** (Recommended) - Modern APT frontend with smooth UI, official checkra1n bootstrap
- **Zebra** - Lightweight and fast, clean interface, community-maintained
- **Cydia** - Classic jailbreak package manager, most compatible with legacy repos

The dialog features:
- Glass-styled UI matching the app theme
- Clear descriptions of each option
- Visual recommendation (★ marker for Sileo)
- Cancel support (close dialog without selection)

### 2. Enhanced Bootstrap Installer

Modified [core/bootstrap.py](core/bootstrap.py) to support all three package managers:

**Key changes**:
- Added `package_manager` parameter to `BootstrapInstaller.__init__()`
- Updated bash script to accept package manager choice as argument
- Added package manager installation step after base bootstrap
- Downloads and installs Zebra or Cydia .deb files when selected
- Falls back to Sileo if download fails

**Package manager URLs**:
```python
_PKG_URLS = {
    "sileo": None,  # Included in checkra1n bootstrap
    "zebra": "https://getzbra.com/repo/dists/stable/main/binary-iphoneos-arm/getzbra_1.1.28_iphoneos-arm.deb",
    "cydia": "https://apt.bingner.com/debs/1443.00/cydia_1.1.36_iphoneos-arm.deb",
}
```

**Installation flow**:
1. Download checkra1n base bootstrap (APT system + core utilities)
2. Mount root disk image
3. Extract base bootstrap files
4. If Zebra or Cydia selected:
   - Download .deb package
   - Extract to mounted filesystem using `dpkg-deb -x`
5. Configure launchd.plist
6. Unmount and cleanup

### 3. Updated Emulator Panel

Modified [gui/emulator_panel.py](gui/emulator_panel.py):

- Changed button text from "Install Sileo" to "Install Bootstrap"
- Added dynamic status messages based on chosen package manager
- `set_bootstrap_running(package_manager)` - Shows "Installing Sileo/Zebra/Cydia..."
- `set_bootstrap_done(success)` - Shows "Sileo/Zebra/Cydia Installed" or retry message
- Tracks chosen package manager for accurate status updates

### 4. Updated Main App

Modified [gui/app.py](gui/app.py):

- Import `PackageManagerDialog`
- `_on_bootstrap_clicked()` now:
  1. Shows package manager selection dialog
  2. Gets user's choice (or returns if cancelled)
  3. Passes choice to `BootstrapInstaller(package_manager=choice)`
  4. Updates UI with chosen package manager name

## How It Works

### User Flow

```
User clicks "Install Bootstrap"
    ↓
Package Manager Dialog opens
    ↓
User selects: Sileo / Zebra / Cydia
    ↓
Dialog closes, returns choice
    ↓
BootstrapInstaller starts with chosen package manager
    ↓
Downloads checkra1n base bootstrap (~80MB)
    ↓
Mounts root disk image (tries multiple strategies)
    ↓
Extracts base bootstrap files
    ↓
If Zebra or Cydia chosen:
  - Downloads package manager .deb (~5-10MB)
  - Extracts .deb to filesystem
    ↓
Configures launchd.plist
    ↓
Unmounts and cleans up
    ↓
"[Package Manager] Installed" message shown
    ↓
Emulator can be launched with chosen package manager
```

### Package Manager Details

#### Sileo
- **Included**: Already in checkra1n bootstrap
- **Size**: No extra download
- **Features**: Modern UI, native depiction support, fast
- **Best for**: Most users, recommended default

#### Zebra
- **Download**: https://getzbra.com/repo/
- **Size**: ~8MB .deb
- **Features**: Lightweight, clean UI, good performance
- **Best for**: Users wanting minimal overhead

#### Cydia
- **Download**: https://apt.bingner.com/
- **Size**: ~6MB .deb
- **Features**: Classic interface, maximum repo compatibility
- **Best for**: Users familiar with classic jailbreak tools

## Technical Details

### Bash Script Changes

The bash script now accepts a package manager argument:

```bash
PKG_MANAGER="$1"
[ -z "$PKG_MANAGER" ] && PKG_MANAGER="sileo"
```

And handles installation accordingly:

```bash
case "$PKG_MANAGER" in
    sileo)
        log_info "Using Sileo (included in checkra1n bootstrap)"
        ;;
    zebra)
        log_info "Installing Zebra package manager..."
        PKG_URL="__ZEBRA_URL__"
        curl -L -o "$PKG_FILE" "$PKG_URL"
        sudo -n dpkg-deb -x "$PKG_FILE" "$MOUNT_POINT"
        ;;
    cydia)
        log_info "Installing Cydia package manager..."
        PKG_URL="__CYDIA_URL__"
        curl -L -o "$PKG_FILE" "$PKG_URL"
        sudo -n dpkg-deb -x "$PKG_FILE" "$MOUNT_POINT"
        ;;
esac
```

### Progress Tracking

Updated progress steps:

| Step | Action | Progress % |
|------|--------|-----------|
| `checking_tools` | Check sudo, jq, curl | 5% |
| `downloading` | Download checkra1n bootstrap | 15% |
| `mounting` | Mount root disk image | 35% |
| `extracting` | Extract bootstrap files | 55% |
| `configuring` | Configure launchd.plist | 70% |
| `package_manager` | Install package manager | 85% |
| `cleanup` | Unmount and cleanup | 95% |
| `done` | Complete | 100% |

## Fixes

### Bootstrap Installation Issues

The previous "install sileo not working" issue has been addressed:

1. **Better error handling**: All commands check exit codes
2. **Multiple mount strategies**: Tries direct mount, kpartx, apfs-fuse
3. **Clear error messages**: Tells user exactly what failed and how to fix
4. **Fallback support**: If Zebra/Cydia download fails, keeps Sileo

### Common Issues Fixed

**Issue**: "sudo requires a password"
- **Fix**: Clear instructions to set up passwordless sudo in WSL
- **Message**: Shows exact command to run: `echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER`

**Issue**: "Could not mount root disk image"
- **Fix**: Tries multiple mounting strategies automatically
- **Message**: Shows manual installation steps if all strategies fail

**Issue**: "Bootstrap download failed"
- **Fix**: Checks for network connectivity, validates downloaded file
- **Message**: Clear error with troubleshooting steps

## Testing

### Test Scenarios

1. **Sileo installation** (default):
   ```
   - Click "Install Bootstrap"
   - Select Sileo (★ Recommended)
   - Wait for installation (~2-3 minutes)
   - Launch emulator
   - Open Sileo app
   ```

2. **Zebra installation**:
   ```
   - Click "Install Bootstrap"
   - Select Zebra
   - Wait for installation + Zebra download (~3-4 minutes)
   - Launch emulator
   - Open Zebra app
   ```

3. **Cydia installation**:
   ```
   - Click "Install Bootstrap"
   - Select Cydia
   - Wait for installation + Cydia download (~3-4 minutes)
   - Launch emulator
   - Open Cydia app
   ```

4. **Cancellation**:
   ```
   - Click "Install Bootstrap"
   - Close dialog without selecting
   - Nothing happens, button remains "Install Bootstrap"
   ```

### Verification Steps

After installation, verify the package manager is working:

1. Launch Inferno emulator
2. Wait for iOS to boot (~2-3 minutes)
3. Look for package manager icon on springboard:
   - **Sileo**: Purple gradient icon
   - **Zebra**: Black and white zebra icon
   - **Cydia**: Brown icon with stylized "C"
4. Open the app and check that it loads repos correctly
5. Try installing a test package (e.g., "NewTerm 2")

## Future Enhancements

Possible improvements:

1. **Package manager switching**: Allow changing package managers after installation
2. **Custom repos**: Pre-configure favorite repos during installation
3. **Faster extraction**: Use parallel extraction for .deb files
4. **Progress details**: Show current file being extracted
5. **Installer**: Alternative bootstrap sources (Procursus, Odyssey, etc.)

## Files Modified

| File | Changes |
|------|---------|
| [core/bootstrap.py](core/bootstrap.py) | Added package manager support, updated script |
| [gui/emulator_panel.py](gui/emulator_panel.py) | Dynamic button text, package manager tracking |
| [gui/app.py](gui/app.py) | Show dialog, pass choice to installer |
| [gui/package_manager_dialog.py](gui/package_manager_dialog.py) | New file - package manager selection dialog |

## Summary

✅ **Package manager choice dialog implemented**
✅ **Support for Sileo, Zebra, and Cydia**
✅ **Automatic download and installation**
✅ **Improved error handling and feedback**
✅ **Dynamic UI updates based on choice**
✅ **Fallback to Sileo if download fails**

Users now have full control over which package manager they want to use on their Inferno emulator! 🎉

## Usage

1. Stop the Inferno emulator if running
2. Click **"Install Bootstrap"** in the Emulator panel
3. Choose your preferred package manager:
   - **Sileo** (recommended) - Modern, fast, official
   - **Zebra** - Lightweight alternative
   - **Cydia** - Classic interface
4. Wait for installation to complete (~2-4 minutes)
5. Launch the emulator
6. Find your chosen package manager on the home screen

That's it! You can now install tweaks and apps using your preferred package manager. 🚀
