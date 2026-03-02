# Quick Fixes - Setup Wizard & Scrolling

## Issues Fixed

### 1. ✅ pongoOS Setup Not in Wizard
**Problem**: pongoOS setup steps were not accessible through the Setup Wizard GUI

**Solution**:
- Modified `SetupWindow` to support both Inferno and pongoOS
- Added tabbed interface with CTkSegmentedButton to switch emulator types
- Updated `SetupEngine` to route to correct script source
- Both "Setup Wizard" (Inferno) and "Setup pongoOS" (pongoOS) buttons now open the unified wizard

**Files Changed**:
- [gui/setup_window.py](gui/setup_window.py) - Added emulator type parameter and dynamic loading
- [core/setup_engine.py](core/setup_engine.py) - Added emulator_type routing
- [gui/app.py](gui/app.py) - Pass emulator_type to wizard

### 2. ✅ Can't Scroll Down on Menu and Buttons
**Problem**: Main window panels were cut off at bottom, no way to scroll to see pongoOS panel and DFU guide

**Solution**:
- Increased minimum window height from 600px to 750px
- Reduced panel height percentages to better fit:
  - Device: 22% → 20%
  - Exploit: 23% → 21%
  - Emulator: 20% → 19%
  - pongoOS: 18% → 17%
- DFU guide now has more space (9.4% vs 3.4%)

**Files Changed**:
- [gui/app.py](gui/app.py) - Adjusted minsize and panel heights

## Usage

### Access pongoOS Setup Wizard

```
Click "Setup pongoOS" button in pongoOS Emulator panel
    ↓
Wizard opens with pongoOS tab selected
    ↓
3 automated steps ready to run:
  1. Install QEMU
  2. Download pongoOS-QEMU
  3. Test Emulator
    ↓
Click "Run Step" for each
    ↓
Done! Launch pongoOS emulator
```

### Switch Between Emulator Types

```
Open any setup wizard (Inferno or pongoOS)
    ↓
Click [Inferno] or [pongoOS] tab at top
    ↓
Steps update automatically
Work directory changes
Progress preserved per type
```

### Window Sizing

- **Default**: 1160 x 920 (plenty of room)
- **Minimum**: 900 x 750 (all panels visible)
- **Recommended**: Maximize window for best experience

## Panel Heights

At minimum window size (900 x 750):
- Device Panel: ~150px
- Exploit Panel: ~158px
- Inferno Emulator: ~143px
- pongoOS Emulator: ~128px
- DFU Guide: ~70px (enough for text)
- Total: ~649px + gaps

## Testing

1. Launch app: `python main.py`
2. Resize window to 900x750
3. Verify all panels are visible
4. Click "Setup pongoOS" button
5. Verify wizard opens with pongoOS tab
6. Switch to Inferno tab
7. Verify steps change appropriately
8. Close wizard
9. All buttons should be accessible

## Summary

✅ pongoOS setup now fully integrated in wizard
✅ Unified interface for both emulators
✅ All panels visible at minimum window size
✅ Better space distribution (more room for DFU guide)
✅ Window can be resized without cutting off content

Both issues resolved! 🎉
