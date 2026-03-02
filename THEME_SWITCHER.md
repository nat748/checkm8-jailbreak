# Theme Switcher - Dark Mode / Light Mode

## Overview

The checkm8 GUI now includes a theme switcher that allows users to toggle between Dark Mode (original aesthetic) and Light Mode (iOS Control Center style).

## Features

✅ **One-click theme switching** - Button in the header
✅ **Persistent preference** - Theme choice saved across sessions
✅ **Two complete themes** - Dark mode and light mode
✅ **Automatic restart** - App restarts to apply theme fully
✅ **Visual feedback** - Icons change (☀ sun / ☾ moon)

## How to Use

### Switch Theme

1. Look for the theme button in the top-right corner of the app (next to "About")
2. **Dark Mode**: Shows ☀ (sun icon) - click to switch to light
3. **Light Mode**: Shows ☾ (moon icon) - click to switch to dark
4. App will restart automatically to apply the new theme

### Icon Meanings

- **☀ Sun**: Currently in Dark Mode, click to enable Light Mode
- **☾ Moon**: Currently in Light Mode, click to enable Dark Mode

## Theme Details

### Dark Theme (Default)

**Original checkm8 aesthetic**:
- Background: Deep dark blue `#08081a`
- Glass panels: Dark purple-blue `#16163a`
- Text: Light gray `#e2e8f0`
- Accent: Purple `#8b5cf6`
- Corners: 22px radius
- Borders: 1px visible
- Blobs: Dark purple/blue/rose tones

**Use when**:
- You prefer dark interfaces
- Working in low-light environments
- Want the original aesthetic
- Need less eye strain at night

### Light Theme

**iOS Control Center style**:
- Background: Light blue `#5599dd`
- Glass panels: Soft blue-white `#c8ddf0`
- Text: Dark `#1d1d1f` (iOS style)
- Accent: iOS blue `#007aff`
- Corners: 28px radius (more rounded)
- Borders: 0px (no visible borders)
- Blobs: Light blue gradient tones

**Use when**:
- You prefer light interfaces
- Working in bright environments
- Want modern iOS aesthetic
- Need high contrast for readability

## Implementation

### Theme Storage

Themes are defined in [config/themes.py](config/themes.py):

```python
DARK_THEME = {
    "name": "dark",
    "COLOR_BG": "#08081a",
    "COLOR_GLASS": "#16163a",
    # ... all color definitions
}

LIGHT_THEME = {
    "name": "light",
    "COLOR_BG": "#5599dd",
    "COLOR_GLASS": "#c8ddf0",
    # ... all color definitions
}
```

### Preference Persistence

Theme preference is saved to `~/.checkm8/theme.txt`:
- Contains either "dark" or "light"
- Loaded at app startup
- Updated when theme is toggled

### Startup Theme Loading

In [main.py](main.py):
1. Load theme preference from file
2. Apply theme colors to constants module
3. Update fluid background colors
4. Create GUI with selected theme

### Theme Toggle Process

When user clicks theme button:
1. Toggle current theme (dark → light or light → dark)
2. Save new preference to file
3. Log message to user
4. Restart app after 1 second delay
5. New theme is applied on restart

### Restart Mechanism

```python
def _restart_app(self):
    import sys, os
    self.destroy()  # Close current window
    os.execl(sys.executable, sys.executable, *sys.argv)  # Restart Python
```

## Files Modified/Created

### New Files
- [config/themes.py](config/themes.py) - Theme definitions and management

### Modified Files
- [main.py](main.py) - Load and apply theme at startup
- [gui/app.py](gui/app.py) - Theme switcher button and toggle handler
- [config/constants.py](config/constants.py) - Default to dark theme

## Technical Details

### Why Restart?

The app restarts when changing themes because:
- CustomTkinter sets colors at widget creation time
- Colors can't be changed dynamically after widgets are created
- A restart ensures all colors update consistently

### Theme Application Order

```
Startup:
  1. main.py loads theme preference
  2. Theme colors applied to constants module
  3. Fluid background colors updated
  4. GUI created with theme colors

Toggle:
  1. User clicks theme button
  2. Theme is toggled in memory
  3. New preference saved to file
  4. App restarts (os.execl)
  5. On restart, new theme is loaded (step 1)
```

### Color Mapping

All color constants are updated:
- `COLOR_BG` - Window background
- `COLOR_GLASS` - Panel backgrounds
- `COLOR_GLASS_LIGHT` - Hover/active states
- `COLOR_GLASS_BORDER` - Panel borders
- `COLOR_ACCENT` - Interactive elements
- `COLOR_TEXT` - Primary text
- `COLOR_TEXT_DIM` - Secondary text
- Status colors (SUCCESS/WARNING/ERROR/INFO)

### Fluid Background

Background blob colors and alpha values change with theme:
- **Dark**: Lower alpha (170-100), dark purple/blue tones
- **Light**: Higher alpha (200-160), light blue gradient tones

## Comparison

| Feature | Dark Theme | Light Theme |
|---------|-----------|-------------|
| **Background** | `#08081a` (very dark) | `#5599dd` (light blue) |
| **Glass** | `#16163a` (dark purple) | `#c8ddf0` (light blue-white) |
| **Text** | `#e2e8f0` (light gray) | `#1d1d1f` (dark) |
| **Accent** | `#8b5cf6` (purple) | `#007aff` (iOS blue) |
| **Corners** | 22px | 28px |
| **Borders** | 1px visible | 0px (none) |
| **Style** | Original moody | iOS modern |
| **Best for** | Night/low light | Day/bright light |

## User Feedback

The app shows a log message when theme is toggled:
```
✓ Switched to Light Mode.
ℹ Restarting app to apply theme...
```

After 1 second, the app restarts with the new theme applied.

## Future Enhancements

Possible improvements:
1. **Smooth transition** - Fade between themes without restart
2. **Auto theme** - Switch based on system time (dark at night)
3. **Custom themes** - User-defined color schemes
4. **Theme preview** - See theme before applying
5. **Per-component** - Different themes for different panels

## Troubleshooting

### Theme doesn't persist
- Check if `~/.checkm8/theme.txt` file is writable
- Verify file contains "dark" or "light"

### Theme button not visible
- Check header panel is rendered
- Verify button is packed correctly

### Colors don't update
- Ensure app restarts after toggling
- Check constants module is updated before GUI creation
- Verify theme.txt contains correct value

### App doesn't restart
- Check for errors in restart code
- Verify sys.executable and sys.argv are correct
- Try manually restarting the app

## Summary

✅ **Dark Mode**: Original moody aesthetic with deep blues and purples
✅ **Light Mode**: Modern iOS Control Center style with soft blues
✅ **One-click toggle**: Button in header with visual icons
✅ **Persistent**: Theme preference saved to `~/.checkm8/theme.txt`
✅ **Automatic**: App restarts to apply theme fully
✅ **Complete**: All colors, borders, corners, and blobs update

Users can now choose their preferred visual style! 🎨
