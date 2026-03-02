"""
checkm8 Jailbreak Tool - Entry Point

A Windows GUI application implementing the checkm8 bootrom exploit
for Apple devices with A5-A11 chips (iPhone 4S through iPhone X).

Based on the publicly available research by axi0mX.
For educational and security research purposes only.
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk


def check_dependencies():
    """Verify required packages are installed."""
    missing = []

    try:
        import usb.core
    except ImportError:
        missing.append("pyusb")

    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        sys.exit(1)


def main():
    check_dependencies()

    # Load theme preference before creating GUI
    from config.themes import load_theme_preference, get_current_theme
    load_theme_preference()
    theme = get_current_theme()

    # Apply theme to constants module
    import config.constants as constants
    constants.COLOR_BG = theme["COLOR_BG"]
    constants.COLOR_GLASS = theme["COLOR_GLASS"]
    constants.COLOR_GLASS_LIGHT = theme["COLOR_GLASS_LIGHT"]
    constants.COLOR_GLASS_BORDER = theme["COLOR_GLASS_BORDER"]
    constants.COLOR_GLASS_GLOW = theme["COLOR_GLASS_GLOW"]
    constants.COLOR_ACCENT = theme["COLOR_ACCENT"]
    constants.COLOR_ACCENT_HOVER = theme["COLOR_ACCENT_HOVER"]
    constants.COLOR_ACCENT_DIM = theme["COLOR_ACCENT_DIM"]
    constants.COLOR_SUCCESS = theme["COLOR_SUCCESS"]
    constants.COLOR_WARNING = theme["COLOR_WARNING"]
    constants.COLOR_ERROR = theme["COLOR_ERROR"]
    constants.COLOR_INFO = theme["COLOR_INFO"]
    constants.COLOR_TEXT = theme["COLOR_TEXT"]
    constants.COLOR_TEXT_DIM = theme["COLOR_TEXT_DIM"]
    constants.COLOR_TEXT_BRIGHT = theme["COLOR_TEXT_BRIGHT"]
    constants.BLOB_COLORS = theme["BLOB_COLORS"]

    # Apply radius/border based on theme
    if theme["name"] == "light":
        constants.GLASS_RADIUS = 28
        constants.GLASS_BORDER_WIDTH = 0
    else:
        constants.GLASS_RADIUS = 22
        constants.GLASS_BORDER_WIDTH = 1

    # CustomTkinter appearance
    ctk.set_appearance_mode(theme["name"])
    ctk.set_default_color_theme("blue")

    # Also update fluid_background module
    import gui.fluid_background as fluid_bg
    fluid_bg.BG_RGB = theme["BG_RGB"]
    fluid_bg._BLOB_DEFS = [
        (600, 0, 0.20, 0.25, 0.22, 0.16, 0.0, theme["BLOB_ALPHA"][0]),
        (700, 1, 0.65, 0.35, 0.16, 0.24, 1.0, theme["BLOB_ALPHA"][1]),
        (500, 2, 0.82, 0.18, 0.20, 0.14, 2.0, theme["BLOB_ALPHA"][2]),
        (550, 3, 0.30, 0.70, 0.26, 0.18, 3.0, theme["BLOB_ALPHA"][3]),
        (650, 4, 0.08, 0.60, 0.14, 0.20, 4.0, theme["BLOB_ALPHA"][4]),
        (400, 5, 0.50, 0.12, 0.18, 0.22, 5.0, theme["BLOB_ALPHA"][5]),
    ]

    from gui.app import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
