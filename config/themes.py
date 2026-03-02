"""
Theme management for checkm8 GUI.

Supports both light (iOS style) and dark themes with smooth transitions.
"""

# ── Light Theme (iOS Control Center) ──────────────────────────────
LIGHT_THEME = {
    "name": "light",
    "COLOR_BG": "#5599dd",
    "COLOR_GLASS": "#c8ddf0",  # Less bright, more blue tint
    "COLOR_GLASS_LIGHT": "#dae8f5",  # Softer light glass
    "COLOR_GLASS_BORDER": "#b8cfe8",  # Visible but subtle border
    "COLOR_GLASS_GLOW": "#ffffff",
    "COLOR_ACCENT": "#007aff",
    "COLOR_ACCENT_HOVER": "#0051d5",
    "COLOR_ACCENT_DIM": "#5ac8fa",
    "COLOR_SUCCESS": "#30d158",
    "COLOR_WARNING": "#ff9f0a",
    "COLOR_ERROR": "#ff453a",
    "COLOR_INFO": "#5ac8fa",
    "COLOR_TEXT": "#1d1d1f",
    "COLOR_TEXT_DIM": "#6e6e73",
    "COLOR_TEXT_BRIGHT": "#000000",
    "BG_RGB": (85, 153, 221),  # Light blue
    "BLOB_COLORS": [
        (85, 153, 221),   # iOS blue
        (90, 200, 250),   # Light sky blue
        (135, 180, 255),  # Periwinkle blue
        (100, 170, 230),  # Medium blue
        (120, 190, 240),  # Light azure
        (75, 145, 210),   # Deep sky blue
    ],
    "BLOB_ALPHA": [200, 190, 180, 170, 190, 160],
}

# ── Dark Theme (Original) ──────────────────────────────────────────
DARK_THEME = {
    "name": "dark",
    "COLOR_BG": "#08081a",
    "COLOR_GLASS": "#16163a",
    "COLOR_GLASS_LIGHT": "#1c1c48",
    "COLOR_GLASS_BORDER": "#5858a8",
    "COLOR_GLASS_GLOW": "#7070c0",
    "COLOR_ACCENT": "#8b5cf6",
    "COLOR_ACCENT_HOVER": "#a78bfa",
    "COLOR_ACCENT_DIM": "#6d28d9",
    "COLOR_SUCCESS": "#34d399",
    "COLOR_WARNING": "#fbbf24",
    "COLOR_ERROR": "#f87171",
    "COLOR_INFO": "#94a3b8",
    "COLOR_TEXT": "#e2e8f0",
    "COLOR_TEXT_DIM": "#7080a8",
    "COLOR_TEXT_BRIGHT": "#f8fafc",
    "BG_RGB": (8, 8, 26),  # Very dark
    "BLOB_COLORS": [
        (70, 30, 160),    # deep blue-purple
        (35, 75, 195),    # ocean blue
        (175, 45, 110),   # rose
        (20, 130, 130),   # teal
        (105, 50, 185),   # violet
        (170, 90, 35),    # warm amber
    ],
    "BLOB_ALPHA": [170, 150, 140, 120, 140, 100],
}

# Default theme
_current_theme = DARK_THEME


def get_current_theme():
    """Get the currently active theme."""
    return _current_theme


def set_theme(theme_name):
    """Set the active theme."""
    global _current_theme
    if theme_name == "light":
        _current_theme = LIGHT_THEME
    else:
        _current_theme = DARK_THEME
    return _current_theme


def toggle_theme():
    """Toggle between light and dark themes."""
    global _current_theme
    if _current_theme["name"] == "dark":
        _current_theme = LIGHT_THEME
    else:
        _current_theme = DARK_THEME
    return _current_theme


def get_color(color_name):
    """Get a color from the current theme."""
    return _current_theme.get(color_name)


def save_theme_preference():
    """Save theme preference to file."""
    try:
        import os
        config_dir = os.path.expanduser("~/.checkm8")
        os.makedirs(config_dir, exist_ok=True)
        theme_file = os.path.join(config_dir, "theme.txt")
        with open(theme_file, "w") as f:
            f.write(_current_theme["name"])
    except Exception:
        pass  # Silently fail if can't save


def load_theme_preference():
    """Load theme preference from file."""
    try:
        import os
        theme_file = os.path.expanduser("~/.checkm8/theme.txt")
        if os.path.exists(theme_file):
            with open(theme_file, "r") as f:
                theme_name = f.read().strip()
                set_theme(theme_name)
    except Exception:
        pass  # Use default if can't load
