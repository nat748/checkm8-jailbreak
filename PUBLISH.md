# Publishing to GitHub Releases

Quick guide to publish checkm8 packages to your GitHub repository.

## Prerequisites

1. **GitHub repository** - Create one at https://github.com/new
2. **Git configured** - Your GitHub username and email set up
3. **Remote added** - Your repo linked as origin

## One-Time Setup

### 1. Create GitHub Repository

```bash
# On GitHub, create a new repository called "checkm8-jailbreak"
# Then link it:

cd n:/checkm8-jailbreak
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/checkm8-jailbreak.git
git push -u origin main
```

### 2. Enable GitHub Actions

GitHub Actions should be enabled by default. If not:
1. Go to your repo on GitHub
2. Click **Settings** → **Actions** → **General**
3. Select **"Allow all actions and reusable workflows"**
4. Click **Save**

## Publish a Release

### Option 1: Quick Script (Recommended)

**On Windows (PowerShell):**
```powershell
.\release.ps1 1.0.0 "Initial release with Inferno support"
```

**On macOS/Linux (bash):**
```bash
chmod +x release.sh
./release.sh 1.0.0 "Initial release with Inferno support"
```

This automatically:
- Creates a git tag `v1.0.0`
- Pushes to GitHub
- Triggers the build workflow
- Shows you the links to monitor progress

### Option 2: Manual Steps

```bash
# 1. Commit your changes
git add .
git commit -m "Prepare v1.0.0 release"
git push origin main

# 2. Create and push the tag
git tag -a v1.0.0 -m "Release v1.0.0

- Liquid glass UI with animated background
- USB DFU device detection and exploitation
- Inferno iPhone 11 emulator integration
- Automated setup wizard for all platforms
- One-click Sileo bootstrap installer
- Credits window with open-source licenses"

git push origin v1.0.0
```

### 3. Monitor the Build

After pushing the tag:

1. Go to: `https://github.com/YOUR_USERNAME/checkm8-jailbreak/actions`
2. You'll see **"Build & Release"** workflow running
3. It builds on 3 platforms in parallel (~10-20 minutes total):
   - 🪟 Windows (creates .exe and installer)
   - 🍎 macOS (creates .app and .dmg)
   - 🐧 Linux (creates binary and .deb)

### 4. Release is Ready!

When all builds complete:
1. Go to: `https://github.com/YOUR_USERNAME/checkm8-jailbreak/releases`
2. Your release will be there with all platform packages attached
3. Share the release URL!

## What Gets Published

Each release includes:

### Windows
- `checkm8-windows-portable.zip` - Portable version (extract and run)

### macOS
- `checkm8-macos.dmg` - Disk image (drag to Applications)

### Linux
- `checkm8-linux-x86_64.tar.gz` - Portable tarball

## Troubleshooting

### "fatal: not a git repository"

```bash
cd n:/checkm8-jailbreak
git init
git add .
git commit -m "Initial commit"
```

### "fatal: 'origin' does not appear to be a git repository"

```bash
# Add your GitHub repo as origin
git remote add origin https://github.com/YOUR_USERNAME/checkm8-jailbreak.git
git push -u origin main
```

### "Permission denied" when pushing

You need to authenticate with GitHub. Options:

**Option A: Personal Access Token (Recommended)**
1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Select scopes: `repo` (all), `workflow`
4. Copy the token
5. When Git asks for password, paste the token

**Option B: SSH Key**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to GitHub: https://github.com/settings/keys
cat ~/.ssh/id_ed25519.pub

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/checkm8-jailbreak.git
```

### "Build failed" in GitHub Actions

1. Click on the failed workflow run
2. Expand the failed step to see error
3. Common fixes:
   - Missing icons: Run `python assets/generate_icon.py` and commit
   - Python errors: Check `requirements.txt` is up to date
   - Import errors: Add missing imports to `checkm8.spec`

### "No releases appear"

The release only auto-creates if:
- Tag starts with `v` (e.g., `v1.0.0` not `1.0.0`)
- GitHub Actions completes successfully
- You have `contents: write` permission in the workflow

Check:
```bash
git tag  # Should show v1.0.0
```

## Making Changes After Release

To update a release:

```bash
# Make your changes
git add .
git commit -m "Fix bug in exploit engine"
git push origin main

# Create a new tag (bump version)
git tag -a v1.0.1 -m "Hotfix v1.0.1 - Fix exploit bug"
git push origin v1.0.1
```

GitHub Actions will automatically build v1.0.1 and create a new release.

## Deleting a Release

If you need to redo a release:

```bash
# Delete tag locally
git tag -d v1.0.0

# Delete tag on GitHub
git push origin :refs/tags/v1.0.0

# On GitHub, go to Releases and manually delete the release

# Then recreate with fixes
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Example: Your First Release

```powershell
# Windows PowerShell - Complete first release

# 1. Make sure you're in the project directory
cd n:\checkm8-jailbreak

# 2. Initialize git if needed
git init

# 3. Add all files
git add .
git commit -m "Initial commit - checkm8 GUI v1.0.0"

# 4. Create GitHub repo at https://github.com/new
#    Name it: checkm8-jailbreak

# 5. Link your repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/checkm8-jailbreak.git
git branch -M main
git push -u origin main

# 6. Create and push release tag
.\release.ps1 1.0.0 "Initial release

- Liquid glass UI
- checkm8 exploit for A5-A11 devices
- Inferno emulator integration
- Setup wizard for all platforms
- Sileo bootstrap installer"

# 7. Watch it build:
#    https://github.com/YOUR_USERNAME/checkm8-jailbreak/actions

# 8. Your release will be at:
#    https://github.com/YOUR_USERNAME/checkm8-jailbreak/releases/tag/v1.0.0
```

That's it! Your packages are now publicly available for download.

## Keeping It Private

If you don't want public releases:
1. Make the GitHub repo **private** (Settings → Danger Zone → Change visibility)
2. Releases will only be visible to you and collaborators
3. GitHub Actions still works on private repos (with free tier limits)

## Next Steps

- 📝 Add a `CHANGELOG.md` to track changes between versions
- 🔒 Consider code signing certificates for Windows/macOS
- 🤖 Add automated testing before release
- 📊 Track download statistics on GitHub Insights
- 💬 Set up GitHub Discussions for user support

## Getting Help

- GitHub Actions docs: https://docs.github.com/en/actions
- Release docs: https://docs.github.com/en/repositories/releasing-projects-on-github
- Git tutorial: https://git-scm.com/doc

Good luck with your release! 🚀
