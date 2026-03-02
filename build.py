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


def build_windows_installer():
    """Create Windows installer using Inno Setup (if available)."""
    if not IS_WIN:
        print("Skipping Windows installer (not on Windows)")
        return

    inno_script = ROOT / 'installer_windows.iss'
    if not inno_script.exists():
        print("Inno Setup script not found, skipping installer creation")
        return

    # Try to find Inno Setup
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc = None
    for path in inno_paths:
        if Path(path).exists():
            iscc = path
            break

    if iscc:
        print("\nCreating Windows installer...")
        run([iscc, str(inno_script)])
        print("✓ Windows installer created")
    else:
        print("Inno Setup not found - skipping installer creation")
        print("  Install from: https://jrsoftware.org/isdl.php")


def build_macos_pkg():
    """Create macOS .pkg installer."""
    if not IS_MAC:
        print("Skipping macOS .pkg (not on macOS)")
        return

    app_path = DIST / 'checkm8.app'
    if not app_path.exists():
        print("App bundle not found - build with PyInstaller first")
        return

    pkg_path = DIST / 'checkm8-1.0.0.pkg'
    print("\nCreating macOS .pkg installer...")

    # Use pkgbuild to create a simple installer
    run([
        'pkgbuild',
        '--root', str(DIST),
        '--identifier', 'com.checkm8.gui',
        '--version', '1.0.0',
        '--install-location', '/Applications',
        str(pkg_path)
    ])

    if pkg_path.exists():
        print(f"✓ macOS .pkg created: {pkg_path}")
    else:
        print("✗ Failed to create .pkg")


def build_linux_deb():
    """Create Debian .deb package."""
    if not IS_LINUX:
        print("Skipping .deb package (not on Linux)")
        return

    bin_path = DIST / 'checkm8' / 'checkm8'
    if not bin_path.exists():
        print("Binary not found - build with PyInstaller first")
        return

    print("\nCreating Debian .deb package...")

    # Create debian package structure
    deb_root = BUILD / 'checkm8_1.0.0_amd64'
    deb_root.mkdir(parents=True, exist_ok=True)

    # DEBIAN control directory
    debian_dir = deb_root / 'DEBIAN'
    debian_dir.mkdir(exist_ok=True)

    # Control file
    control = debian_dir / 'control'
    control.write_text(f"""Package: checkm8
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: checkm8 Project
Description: checkm8 bootrom exploit GUI
 A5-A11 bootrom exploit tool with Inferno emulator integration.
 Includes setup wizard for full Inferno installation.
Depends: libusb-1.0-0, python3
""")

    # Install files
    usr_bin = deb_root / 'usr' / 'bin'
    usr_bin.mkdir(parents=True, exist_ok=True)
    shutil.copytree(DIST / 'checkm8', usr_bin / 'checkm8')

    # Desktop entry
    applications = deb_root / 'usr' / 'share' / 'applications'
    applications.mkdir(parents=True, exist_ok=True)
    desktop = applications / 'checkm8.desktop'
    desktop.write_text(f"""[Desktop Entry]
Name=checkm8
Comment=Bootrom exploit tool
Exec=/usr/bin/checkm8/checkm8
Icon=checkm8
Terminal=false
Type=Application
Categories=Utility;System;
""")

    # Icon
    icons = deb_root / 'usr' / 'share' / 'icons' / 'hicolor' / '256x256' / 'apps'
    icons.mkdir(parents=True, exist_ok=True)
    if (ROOT / 'assets' / 'icon.png').exists():
        shutil.copy(ROOT / 'assets' / 'icon.png', icons / 'checkm8.png')

    # Build .deb
    run(['dpkg-deb', '--build', str(deb_root)])

    deb_file = BUILD / 'checkm8_1.0.0_amd64.deb'
    if deb_file.exists():
        # Move to dist
        shutil.move(str(deb_file), DIST / 'checkm8_1.0.0_amd64.deb')
        print(f"✓ Debian package created: {DIST / 'checkm8_1.0.0_amd64.deb'}")
    else:
        print("✗ Failed to create .deb")


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

    # Create platform-specific installers
    if args.all or IS_WIN:
        build_windows_installer()

    if args.all or IS_MAC:
        build_macos_pkg()

    if args.all or IS_LINUX:
        build_linux_deb()

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
