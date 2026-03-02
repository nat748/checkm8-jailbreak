#!/usr/bin/env python3
"""
Build script for checkm8 GUI application.

Creates distributable packages for Windows (.exe), macOS (.app/.pkg),
and Linux (.deb).

Usage:
    python build.py          # Build for current platform
    python build.py --all    # Build all available formats
    python build.py --clean  # Clean build artifacts
"""

import sys
import os
import shutil
import subprocess
import platform
from pathlib import Path

PLATFORM = platform.system().lower()
IS_WIN = PLATFORM == 'windows'
IS_MAC = PLATFORM == 'darwin'
IS_LINUX = PLATFORM == 'linux'

ROOT = Path(__file__).parent
DIST = ROOT / 'dist'
BUILD = ROOT / 'build'


def run(cmd, cwd=None, check=True):
    """Run a shell command."""
    print(f"$ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    return subprocess.run(
        cmd, cwd=cwd, check=check, shell=isinstance(cmd, str)
    )


def clean():
    """Remove build artifacts."""
    print("Cleaning build artifacts...")
    for path in [DIST, BUILD, ROOT / '__pycache__']:
        if path.exists():
            shutil.rmtree(path)
            print(f"  Removed {path}")
    for path in ROOT.rglob('*.pyc'):
        path.unlink()
    for path in ROOT.rglob('__pycache__'):
        if path.is_dir():
            shutil.rmtree(path)
    print("Clean complete.")


def check_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def build_pyinstaller():
    """Build with PyInstaller."""
    print(f"\nBuilding for {PLATFORM}...")
    check_pyinstaller()

    # Run PyInstaller
    run([sys.executable, '-m', 'PyInstaller', 'checkm8.spec', '--clean'])

    if IS_WIN:
        exe_path = DIST / 'checkm8' / 'checkm8.exe'
        if exe_path.exists():
            print(f"\n✓ Windows executable created: {exe_path}")
            print(f"  Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print("✗ Build failed - executable not found")
            return False

    elif IS_MAC:
        app_path = DIST / 'checkm8.app'
        if app_path.exists():
            print(f"\n✓ macOS app bundle created: {app_path}")
        else:
            print("✗ Build failed - app bundle not found")
            return False

    elif IS_LINUX:
        bin_path = DIST / 'checkm8' / 'checkm8'
        if bin_path.exists():
            print(f"\n✓ Linux binary created: {bin_path}")
            # Make executable
            os.chmod(bin_path, 0o755)
        else:
            print("✗ Build failed - binary not found")
            return False

    return True


def build_windows_zip():
    """Create Windows portable ZIP."""
    if not IS_WIN:
        return

    zip_path = DIST / 'checkm8-windows-portable.zip'
    checkm8_dir = DIST / 'checkm8'

    if not checkm8_dir.exists():
        print("Build directory not found")
        return

    print("\nCreating Windows portable ZIP...")
    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', DIST, 'checkm8')

    if zip_path.exists():
        print(f"✓ Windows ZIP created: {zip_path}")
    else:
        print("✗ Failed to create ZIP")


def build_macos_dmg():
    """Create macOS DMG (requires hdiutil on macOS)."""
    if not IS_MAC:
        return

    app_path = DIST / 'checkm8.app'
    if not app_path.exists():
        print("App bundle not found - build with PyInstaller first")
        return

    dmg_path = DIST / 'checkm8-macos.dmg'
    print("\nCreating macOS DMG...")

    # Use hdiutil to create DMG
    run([
        'hdiutil', 'create',
        '-volname', 'checkm8',
        '-srcfolder', str(app_path),
        '-ov',
        '-format', 'UDZO',
        str(dmg_path)
    ])

    if dmg_path.exists():
        print(f"✓ macOS DMG created: {dmg_path}")
    else:
        print("✗ Failed to create DMG")


def build_linux_tarball():
    """Create Linux tarball."""
    if not IS_LINUX:
        return

    bin_path = DIST / 'checkm8' / 'checkm8'
    if not bin_path.exists():
        print("Binary not found - build with PyInstaller first")
        return

    tar_path = DIST / 'checkm8-linux-x86_64.tar.gz'
    print("\nCreating Linux tarball...")

    # Create tarball
    shutil.make_archive(
        str(tar_path.with_suffix('').with_suffix('')),
        'gztar',
        DIST,
        'checkm8'
    )

    if tar_path.exists():
        print(f"✓ Linux tarball created: {tar_path}")
    else:
        print("✗ Failed to create tarball")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Build checkm8 packages')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts')
    parser.add_argument('--all', action='store_true', help='Build all formats')
    args = parser.parse_args()

    if args.clean:
        clean()
        return

    print("╔═══════════════════════════════════════╗")
    print("║  checkm8 Build Script                 ║")
    print("╚═══════════════════════════════════════╝")
    print(f"\nPlatform: {PLATFORM}")
    print(f"Python: {sys.version.split()[0]}")
    print()

    # Build with PyInstaller
    if not build_pyinstaller():
        print("\n✗ Build failed")
        sys.exit(1)

    # Create platform-specific packages
    if IS_WIN:
        build_windows_zip()
    elif IS_MAC:
        build_macos_dmg()
    elif IS_LINUX:
        build_linux_tarball()

    print("\n" + "="*50)
    print("Build complete!")
    print("="*50)
    print(f"\nOutput directory: {DIST}")

    # List created files
    if DIST.exists():
        print("\nCreated files:")
        for item in sorted(DIST.rglob('*')):
            if item.is_file():
                size = item.stat().st_size
                if size > 1024*1024:
                    size_str = f"{size/1024/1024:.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} bytes"
                print(f"  {item.relative_to(DIST)} ({size_str})")


if __name__ == '__main__':
    main()
