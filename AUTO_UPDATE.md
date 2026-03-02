# Auto-Update Feature

The checkm8 GUI includes an automatic update checker that notifies users when new versions are available on GitHub.

## How It Works

1. **Startup Check**: When the app launches, it checks for updates in the background (after 2 seconds)
2. **GitHub Releases**: Queries the GitHub Releases API for the latest version
3. **Version Comparison**: Compares the latest version with the current version (`APP_VERSION` in `config/constants.py`)
4. **Update Notification**: If a new version is available, shows a dialog with release notes and download link
5. **Manual Check**: Users can also click "Check for Updates" in the About window

## Configuration

### 1. Set Your GitHub Repository

Edit [config/constants.py](config/constants.py) and set your GitHub username and repo name:

```python
# GitHub repository for updates
GITHUB_OWNER = "YOUR_USERNAME"  # Replace with your GitHub username
GITHUB_REPO = "checkm8-jailbreak"  # Replace with your repo name
```

**Example:**
```python
GITHUB_OWNER = "johndoe"
GITHUB_REPO = "checkm8-jailbreak"
```

### 2. Publish Releases

The updater checks `https://api.github.com/repos/{owner}/{repo}/releases/latest`

To create a release:
```bash
# Using the release script
.\release.ps1 1.0.1 "Bug fixes and improvements"

# Or manually
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

The GitHub Actions workflow automatically builds and publishes the release.

## Features

### Automatic Background Check
- Checks for updates 2 seconds after app launch
- Non-blocking (doesn't freeze the UI)
- Silent if no updates available
- Handles network errors gracefully

### Update Dialog
When an update is available, shows:
- **New version number**
- **Release notes** (from GitHub release description)
- **Download files** (lists all attached files)
- **"Download Update" button** - Opens the GitHub release page in browser
- **"Remind Me Later" button** - Dismisses the dialog

### Manual Check
- Click **About** button in header
- Click **"Check for Updates"** button
- Works the same as automatic check

## Version Comparison

The updater uses semantic versioning (semver):
- `1.0.1` > `1.0.0` ✓ (update available)
- `1.1.0` > `1.0.9` ✓ (update available)
- `2.0.0` > `1.9.9` ✓ (update available)
- `1.0.0` = `1.0.0` ✗ (no update)

## Disabling Updates

To disable automatic update checks:

**Option 1: Don't configure GitHub repo**
- Leave `GITHUB_OWNER = "YOUR_USERNAME"` (default)
- Update checking will be skipped

**Option 2: Remove the check from code**
- Edit `gui/app.py`
- Remove or comment out the startup check:
```python
# Check for updates in background (non-blocking)
# if GITHUB_OWNER != "YOUR_USERNAME":
#     self.after(2000, self._check_for_updates)
```

## Technical Details

### Update Checker (`core/updater.py`)
```python
UpdateChecker(owner, repo)
  .check_for_updates(callback, timeout=10)
```

- Makes HTTP request to GitHub API
- No authentication required (public repos)
- 10 second timeout
- Returns release info:
  - `version` - Latest version number
  - `url` - GitHub release page URL
  - `notes` - Release notes (markdown)
  - `assets` - List of downloadable files

### Update Dialog (`gui/update_dialog.py`)
- Modal dialog (blocks main window interaction)
- Glass-styled UI matching the app theme
- Scrollable release notes
- Opens browser to GitHub release page

### Integration (`gui/app.py`)
- Background thread for network request
- Queue-based UI updates (thread-safe)
- Single dialog instance (prevents duplicates)

## Example Flow

1. **User launches app**
2. After 2 seconds, background thread starts
3. Queries: `https://api.github.com/repos/johndoe/checkm8-jailbreak/releases/latest`
4. Receives: `{"tag_name": "v1.0.1", "body": "Bug fixes...", ...}`
5. Compares: `"1.0.1"` > current `"1.0.0"` → Update available!
6. Shows dialog with:
   ```
   🎉 New Version Available!
   Version 1.0.1 is now available

   What's New:
   - Fixed USB detection on Windows 11
   - Improved emulator stability
   - Updated Inferno build scripts

   [Download Update]  [Remind Me Later]
   ```
7. User clicks "Download Update"
8. Browser opens to: `https://github.com/johndoe/checkm8-jailbreak/releases/tag/v1.0.1`
9. User downloads new `.zip` / `.dmg` / `.tar.gz` file

## Troubleshooting

### Update check never triggers
- **Check GitHub configuration**: Verify `GITHUB_OWNER` in `config/constants.py` is not `"YOUR_USERNAME"`
- **Check network**: Ensure internet connection is available
- **Check logs**: Look for "Update check failed" messages

### "No updates available" when update exists
- **Check version**: Current version must be lower than released version
- **Check tag format**: GitHub release must use `v1.0.0` format (with `v` prefix)
- **Check public**: Repository must be public (or you need authentication for private repos)

### Dialog doesn't show
- **Check console**: Look for error messages
- **Check multiple instances**: Only one dialog shown at a time
- **Check thread safety**: Dialog creation happens on UI thread via `.after()`

## Advanced: Private Repositories

For private repositories, you need to modify `core/updater.py` to include authentication:

```python
# Add GitHub token to request headers
req = urllib.request.Request(
    self._api_url,
    headers={
        'User-Agent': 'checkm8-updater',
        'Authorization': f'token {YOUR_GITHUB_TOKEN}'
    }
)
```

**Security note**: Never hardcode tokens in the source code. Use environment variables or secure storage.

## API Rate Limits

GitHub API allows:
- **60 requests/hour** for unauthenticated requests (per IP)
- **5000 requests/hour** for authenticated requests

The updater makes:
- **1 request at startup** (after 2 seconds)
- **1 request per manual check** (when user clicks "Check for Updates")

This is well within rate limits for typical usage.

## Future Enhancements

Possible improvements for future versions:

1. **Auto-download**: Download update automatically in background
2. **Auto-install**: Replace files and restart app
3. **Update history**: Show changelog for all versions
4. **Beta channel**: Check for pre-release versions
5. **Update settings**: Configure check frequency, auto-download, etc.
6. **Portable updater**: In-place update without full reinstall

## Files

- `core/updater.py` - Update checking logic
- `gui/update_dialog.py` - Update notification UI
- `gui/app.py` - Integration and callbacks
- `gui/about_window.py` - "Check for Updates" button
- `config/constants.py` - GitHub configuration

## Summary

The auto-updater provides a seamless way for users to stay up-to-date with the latest version. It's:
- **Non-intrusive**: Checks in background, silent if no updates
- **Fast**: 10 second timeout, async operation
- **User-friendly**: Clear dialog with release notes
- **Zero-config**: Just set your GitHub username

Configure it once, and users will always know when new versions are available! 🚀
