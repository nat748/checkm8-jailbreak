#!/bin/bash
# Quick release script for checkm8
# Usage: ./release.sh 1.0.0 "Release message"

set -e

VERSION=$1
MESSAGE=${2:-"Release v$VERSION"}

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version> [message]"
    echo "Example: ./release.sh 1.0.0 \"Initial release\""
    exit 1
fi

# Ensure version starts with v
TAG="v$VERSION"

echo "╔═══════════════════════════════════════╗"
echo "║  checkm8 Release Script                ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "Version: $TAG"
echo "Message: $MESSAGE"
echo ""

# Check if git repo is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: Git working directory is not clean"
    echo "Uncommitted changes:"
    git status --short
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "❌ Error: Tag $TAG already exists"
    echo "Delete it first with: git tag -d $TAG && git push origin :refs/tags/$TAG"
    exit 1
fi

echo "📝 Creating tag $TAG..."
git tag -a "$TAG" -m "$MESSAGE"

echo "📤 Pushing to GitHub..."
git push origin main
git push origin "$TAG"

echo ""
echo "✅ Release $TAG created!"
echo ""
echo "🔨 GitHub Actions is now building packages for all platforms."
echo "   Monitor progress: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo ""
echo "📦 When complete, packages will be at:"
echo "   https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/$TAG"
echo ""
