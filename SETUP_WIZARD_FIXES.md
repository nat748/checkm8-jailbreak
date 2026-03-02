# Setup Wizard Fixes

## Issues Fixed

### 1. **Random Commands Bug** ✅

**Problem**: Setup wizard was executing commands in unexpected ways, appearing "random" or "weird".

**Root cause**:
- Multiline bash scripts with backslash continuations weren't being properly escaped
- Special characters in strings causing interpretation issues
- No error handling (`set -e`) causing scripts to continue after failures
- Line ending issues (Windows `\r\n` vs Unix `\n`)

**Fixes applied**:
1. **Rewrote all scripts to use single-line commands**:
   - Changed from:
     ```bash
     brew install libtool meson ninja \
         pixman snappy vde zstd
     ```
   - To:
     ```bash
     brew install libtool meson ninja pixman snappy vde zstd || exit 1
     ```

2. **Added explicit `echo` prefixes for output markers**:
   - Changed from: `SS_INFO:Installing...`
   - To: `echo "SS_INFO:Installing..."`
   - Prevents shell from trying to execute `SS_INFO:` as a command

3. **Added `set -e` and `set -o pipefail` to all scripts**:
   - Scripts now exit immediately on any error
   - Pipelines fail if any command fails
   - Prevents partial execution

4. **Improved line ending handling**:
   - Clean `\r\n` → `\n` conversion in `setup_engine.py`
   - Added explicit flush after writing to stdin

### 2. **Mac Architecture Support** ✅

**Problem**: No distinction between Intel (x86_64) and Apple Silicon (ARM64) Macs.

**Solution**: Added automatic architecture detection:

```python
def detect_platform():
    """Return 'windows', 'macos', 'macos-arm64', or 'linux'."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        import platform
        if platform.machine() == "arm64":
            return "macos-arm64"
        return "macos"
    return "linux"

def is_macos(platform):
    """Check if platform is any macOS variant."""
    return platform in ("macos", "macos-arm64")
```

**Architecture-specific changes**:

#### Homebrew Paths
- **Intel**: `/usr/local/opt/...`
- **ARM64**: `/opt/homebrew/...`

#### Inferno Build Configuration
- **Intel**:
  ```bash
  ../configure --extra-cflags="-O3 -ffast-math -mtune=native"
  ```

- **ARM64**:
  ```bash
  ../configure \
    --extra-cflags="-I/opt/homebrew/include -O3 -ffast-math -mtune=native" \
    --extra-ldflags="-L/opt/homebrew/lib"
  ```

#### img4lib Build
- **Intel**:
  ```bash
  make LDFLAGS="-L/usr/local/opt/openssl/lib"
  ```

- **ARM64**:
  ```bash
  make LDFLAGS="-L/opt/homebrew/opt/openssl/lib"
  ```

### 3. **Error Handling Improvements** ✅

All commands now explicitly check for errors:

**Before**:
```bash
sudo apt-get update
sudo apt-get install -y build-essential
```

**After**:
```bash
sudo -n apt-get update || exit 1
sudo -n apt-get install -y build-essential || exit 1
```

Every command that can fail has `|| exit 1` to ensure the script stops immediately.

### 4. **Bash Execution Mode** ✅

**Changed**:
```python
# Before
cmd = ["bash"]

# After
cmd = ["bash", "-e"]  # Exit on error
```

Added `-e` flag to bash invocation for extra safety.

## Files Modified

### 1. [core/setup_engine.py](core/setup_engine.py)
- Added `set -e` and `set -o pipefail` to all scripts
- Improved line ending cleanup (`\r\n` → `\n`)
- Added `bash -e` flag for error-on-fail

### 2. [config/setup_steps.py](config/setup_steps.py)
- Added `detect_platform()` with ARM64 Mac support
- Added `is_macos()` helper function
- Rewrote all scripts to use `echo "SS_INFO:..."` format
- Removed multiline backslash continuations
- Added `|| exit 1` after every command
- Updated all platform lists to include `"macos-arm64"`
- Added architecture-specific build configurations

### 3. [config/pongoos_setup.py](config/pongoos_setup.py)
- Same fixes as setup_steps.py
- Added ARM64 Mac support
- Cleaned up all script formatting

## Testing

### Verify Platform Detection

```python
from config.setup_steps import detect_platform

platform = detect_platform()
print(f"Detected: {platform}")
# Intel Mac: "macos"
# Apple Silicon Mac: "macos-arm64"
# Windows: "windows"
# Linux: "linux"
```

### Test Script Execution

```bash
# Run a simple test
python -c "
from core.setup_engine import SetupEngine

def log(level, msg):
    print(f'[{level}] {msg}')

engine = SetupEngine('macos-arm64', '~/InfernoData', log_callback=log)
# Test will detect Apple Silicon and use /opt/homebrew paths
"
```

### Before vs After

**Before (broken)**:
```bash
# Script would execute like this:
brew install libtool meson ninja \
    # Shell interprets backslash incorrectly
    pixman snappy vde zstd
    # Next line runs as separate command!
SS_INFO:Dependencies installed
# Shell tries to execute "SS_INFO:" as a command → error!
```

**After (fixed)**:
```bash
# Script executes cleanly:
echo "SS_INFO:Installing dependencies..."
brew install libtool meson ninja pixman snappy vde zstd || exit 1
echo "SS_INFO:Dependencies installed"
# All commands are explicit and error-checked
```

## Architecture Detection Details

### Detection Method

```python
import platform
arch = platform.machine()
# Intel Mac: "x86_64"
# Apple Silicon Mac: "arm64"
# Linux x86_64: "x86_64"
# Linux ARM64: "aarch64"
```

### Path Differences

| Path Type | Intel Mac | Apple Silicon Mac |
|-----------|-----------|-------------------|
| Homebrew root | `/usr/local` | `/opt/homebrew` |
| Homebrew lib | `/usr/local/lib` | `/opt/homebrew/lib` |
| Homebrew include | `/usr/local/include` | `/opt/homebrew/include` |
| OpenSSL | `/usr/local/opt/openssl` | `/opt/homebrew/opt/openssl` |

### Build Optimizations

**Intel Macs**:
- `-mtune=native` optimizes for specific Intel CPU
- Standard library paths

**Apple Silicon Macs**:
- `-mtune=native` optimizes for M1/M2/M3
- Must explicitly specify Homebrew paths
- Some libraries require additional flags

## Summary

✅ **Fixed random command execution**
✅ **Added Intel vs Apple Silicon detection**
✅ **Improved error handling (all commands check exit code)**
✅ **Cleaned up script formatting (removed backslash continuations)**
✅ **Added `set -e` and `set -o pipefail`**
✅ **Fixed output markers (echo "SS_INFO:...")**
✅ **Updated both Inferno and pongoOS setup wizards**

The setup wizard should now:
1. Detect Mac architecture correctly
2. Use the right Homebrew paths
3. Stop immediately on any error
4. Execute commands in a predictable order
5. Provide clear error messages

Test it: Launch the GUI → Click "Setup Wizard" → Watch it detect your Mac type! 🎉
