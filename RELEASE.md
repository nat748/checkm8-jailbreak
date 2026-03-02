# Release Process

This document explains how to publish new releases of checkm8 to GitHub with automatic builds for all platforms.

## Automatic Builds via GitHub Actions

When you push a version tag (like `v1.0.0`), GitHub Actions automatically:
1. Builds executables for Windows, macOS, and Linux
2. Creates installers (.exe, .dmg, .pkg, .deb)
3. Uploads all packages to a GitHub Release
4. Generates release notes

## Step-by-Step Release Guide

### 1. Update Version Numbers

Before releasing, update the version in these files:

**config/constants.py:**
```python
APP_VERSION = "1.0.0"
```

**checkm8.spec** (macOS bundle version):
```python
'CFBundleShortVersionString': '1.0.0',
'CFBundleVersion': '1.0.0',
```

**build.py** (package versions):
```python
# Update version strings in build_linux_deb() and build_macos_pkg()
```

**installer_windows.iss:**
```iss
#define MyAppVersion "1.0.0"
```

### 2. Commit Changes

```bash
git add .
git commit -m "Release v1.0.0"
git push origin main
```

### 3. Create and Push a Git Tag

```bash
# Create an annotated tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial release with Inferno support"

# Push the tag to GitHub
git push origin v1.0.0
```

**Important:** The tag MUST start with `v` (like `v1.0.0`, `v1.2.3`) to trigger the build workflow.

### 4. Monitor the Build

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You'll see the "Build & Release" workflow running
4. Wait for all three platform builds to complete (~10-20 minutes)

### 5. Verify the Release

Once the workflow completes:
1. Go to the **Releases** section of your repo
2. You should see a new release with your tag
3. Verify all files are attached:
   - `checkm8-windows-portable.zip`
   - `checkm8-1.0.0-setup.exe`
   - `checkm8-macos.dmg`
   - `checkm8-1.0.0.pkg`
   - `checkm8-linux-x86_64.tar.gz`
   - `checkm8_1.0.0_amd64.deb`

### 6. Test the Builds

Download and test each package on the respective platforms before announcing the release.

## Manual Trigger

You can also manually trigger builds without creating a tag:

1. Go to **Actions** → **Build & Release**
2. Click **Run workflow**
3. Select branch and click **Run workflow**

This builds the packages but doesn't create a GitHub Release.

## Hotfix Release Process

For urgent fixes:

```bash
# Make your fixes
git add .
git commit -m "Hotfix: description of fix"

# Create hotfix tag
git tag -a v1.0.1 -m "Hotfix v1.0.1 - Fix critical bug"

# Push
git push origin main
git push origin v1.0.1
```

## Pre-release (Beta)

To mark a release as pre-release:

1. Create a tag with `-beta`, `-rc`, or `-alpha`:
   ```bash
   git tag -a v1.1.0-beta1 -m "Beta release"
   git push origin v1.1.0-beta1
   ```

2. After the build completes, edit the release on GitHub:
   - Check ✅ "This is a pre-release"
   - Update the description to note it's a beta

## Troubleshooting

### "Build failed" - Check logs

1. Go to Actions tab
2. Click on the failed workflow
3. Expand the failed job to see error details

**Common issues:**
- Missing dependencies → Update requirements.txt
- Icon not found → Run `python assets/generate_icon.py` locally first
- PyInstaller errors → Check hiddenimports in checkm8.spec

### "No release created"

The release only auto-creates if you push a tag starting with `v`. Check that:
- Tag format is correct: `v1.0.0` not `1.0.0`
- Tag was pushed: `git push origin v1.0.0`
- Workflow has `permissions: contents: write`

### "Files not uploaded"

Check that the build artifacts were created:
1. Go to the workflow run
2. Check each platform job
3. Look for "Upload to Release" step
4. If it skipped, ensure `if: startsWith(github.ref, 'refs/tags/')` condition is met

## Version Naming Convention

Follow semantic versioning (semver):
- **Major** (v2.0.0): Breaking changes, major new features
- **Minor** (v1.1.0): New features, backwards-compatible
- **Patch** (v1.0.1): Bug fixes only

Examples:
- `v1.0.0` - First stable release
- `v1.1.0` - Added setup wizard feature
- `v1.1.1` - Fixed crash bug
- `v2.0.0` - Complete UI redesign (breaking)
- `v1.2.0-beta1` - Beta for version 1.2.0

## Checklist Before Release

- [ ] All features tested locally
- [ ] Version numbers updated in all files
- [ ] CHANGELOG.md updated (if you have one)
- [ ] README.md reflects new features
- [ ] All tests pass (if applicable)
- [ ] No TODO or FIXME comments in critical code
- [ ] Build script tested locally: `python build.py`
- [ ] Git repo is clean: `git status`
- [ ] Changes committed and pushed
- [ ] Tag created and pushed
- [ ] GitHub Actions build completed successfully
- [ ] All platform packages download and run
- [ ] Release notes look correct

## Rollback

If you need to rollback a release:

1. Delete the tag locally and remotely:
   ```bash
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   ```

2. Delete the GitHub Release:
   - Go to Releases
   - Click the release
   - Click **Delete**

3. Fix the issues and re-release with a new patch version (v1.0.1)

## Example: Complete Release Flow

```bash
# 1. Update version to 1.0.0 in all files
# 2. Commit
git add .
git commit -m "Release v1.0.0"
git push origin main

# 3. Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0

- Liquid glass UI
- Inferno emulator support
- Setup wizard
- Sileo installer"

git push origin v1.0.0

# 4. Wait for GitHub Actions to build
# 5. Check the release at https://github.com/YOUR_USERNAME/checkm8-jailbreak/releases
# 6. Test the downloads
# 7. Announce the release!
```

## Security Considerations

For production releases, consider:

1. **Code signing** (macOS):
   ```bash
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: Your Name" \
     dist/checkm8.app
   ```

2. **Notarization** (macOS):
   ```bash
   xcrun notarytool submit dist/checkm8.dmg \
     --apple-id your@email.com \
     --password app-specific-password \
     --team-id TEAMID
   ```

3. **Checksum verification:**
   ```bash
   cd dist
   sha256sum checkm8-*.* > checksums.txt
   ```
   Then attach `checksums.txt` to the release.

## Support

- Build issues: Check `.github/workflows/build-release.yml`
- Packaging issues: Check `build.py`
- PyInstaller issues: Check `checkm8.spec`
