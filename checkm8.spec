# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for checkm8 GUI application.

Build with: pyinstaller checkm8.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Determine platform
IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = not (IS_WIN or IS_MAC)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include CLAUDE.md for reference
        ('CLAUDE.md', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'customtkinter',
        'usb',
        'usb.core',
        'usb.util',
        'usb.backend',
        'usb.backend.libusb1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='checkm8',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if IS_WIN else 'assets/icon.icns' if IS_MAC else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='checkm8',
)

# macOS: create .app bundle
if IS_MAC:
    app = BUNDLE(
        coll,
        name='checkm8.app',
        icon='assets/icon.icns',
        bundle_identifier='com.checkm8.gui',
        version='1.0.0',
        info_plist={
            'CFBundleName': 'checkm8',
            'CFBundleDisplayName': 'checkm8 Jailbreak Tool',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'Open Source - See About for credits',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
        },
    )
