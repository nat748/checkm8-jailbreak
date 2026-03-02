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

import tkinter
import customtkinter

# Get CustomTkinter assets path
ctk_path = Path(customtkinter.__file__).parent

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include CLAUDE.md for reference
        ('CLAUDE.md', '.'),
        # Include CustomTkinter assets
        (str(ctk_path / 'assets'), 'customtkinter/assets'),
    ],
    hiddenimports=[
        '_tkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'customtkinter',
        'usb',
        'usb.core',
        'usb.util',
        'usb.backend',
        'usb.backend.libusb1',
        'usb.backend.libusb0',
        'usb.backend.openusb',
        'queue',
        'threading',
        'webbrowser',
        'subprocess',
        'pathlib',
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
    icon='assets/icon.ico' if IS_WIN else ('assets/icon.icns' if IS_MAC and Path('assets/icon.icns').exists() else None),
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
        icon='assets/icon.icns' if Path('assets/icon.icns').exists() else None,
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
            'NSPrincipalClass': 'NSApplication',
            'LSApplicationCategoryType': 'public.app-category.utilities',
        },
    )
