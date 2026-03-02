# Quick release script for checkm8 (PowerShell)
# Usage: .\release.ps1 1.0.0 "Release message"

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"

if ($Message -eq "") {
    $Message = "Release v$Version"
}

$Tag = "v$Version"

Write-Host "╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  checkm8 Release Script                ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Version: $Tag" -ForegroundColor Yellow
Write-Host "Message: $Message" -ForegroundColor Yellow
Write-Host ""

# Check if git repo is clean
$status = git status --porcelain
if ($status) {
    Write-Host "⚠️  Warning: Git working directory is not clean" -ForegroundColor Yellow
    Write-Host "Uncommitted changes:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $response = Read-Host "Continue anyway? [y/N]"
    if ($response -notmatch '^[Yy]$') {
        exit 1
    }
}

# Check if tag already exists
$tagExists = git rev-parse $Tag 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "❌ Error: Tag $Tag already exists" -ForegroundColor Red
    Write-Host "Delete it first with: git tag -d $Tag; git push origin :refs/tags/$Tag" -ForegroundColor Red
    exit 1
}

Write-Host "📝 Creating tag $Tag..." -ForegroundColor Green
git tag -a $Tag -m $Message

Write-Host "📤 Pushing to GitHub..." -ForegroundColor Green
git push origin main
git push origin $Tag

$repoUrl = git config --get remote.origin.url
$repoPath = if ($repoUrl -match 'github.com[:/](.+)\.git') { $matches[1] } else { "" }

Write-Host ""
Write-Host "✅ Release $Tag created!" -ForegroundColor Green
Write-Host ""
Write-Host "🔨 GitHub Actions is now building packages for all platforms." -ForegroundColor Cyan
Write-Host "   Monitor progress: https://github.com/$repoPath/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 When complete, packages will be at:" -ForegroundColor Cyan
Write-Host "   https://github.com/$repoPath/releases/tag/$Tag" -ForegroundColor Cyan
Write-Host ""
