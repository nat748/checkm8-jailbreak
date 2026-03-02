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

    # CustomTkinter appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    from gui.app import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
