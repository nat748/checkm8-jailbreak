"""
pongoOS emulator setup steps.

Much simpler than Inferno - just download/build pongoOS and run with QEMU.
"""

import sys


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


PONGOOS_REPO = "https://github.com/karamzaki/pongoOS-QEMU.git"

# checkra1n Debian repo provides ld64 and cctools-strip for Linux cross-compilation
CHECKRA1N_REPO_LINE = "deb https://assets.checkra.in/debian /"
CHECKRA1N_KEY_URL = "https://assets.checkra.in/debian/archive.key"

# pongoOS setup steps
PONGOOS_STEPS = [
    {
        "id": "pongo_deps",
        "name": "Install Dependencies",
        "description": "Install build tools and QEMU dependencies",
        "platforms": ["windows", "linux", "macos", "macos-arm64"],
        "automated": True,
    },
    {
        "id": "pongo_qemu",
        "name": "Build UTMapp QEMU",
        "description": "Build patched QEMU with pongoOS memory layout",
        "platforms": ["windows", "linux", "macos", "macos-arm64"],
        "automated": True,
    },
    {
        "id": "pongo_toolchain",
        "name": "Setup Toolchain",
        "description": "Install clang, ld64, and cctools-strip from checkra1n repo",
        "platforms": ["windows", "linux"],
        "automated": True,
    },
    {
        "id": "pongo_download",
        "name": "Clone & Build pongoOS",
        "description": "Clone pongoOS-QEMU and build from source",
        "platforms": ["windows", "linux", "macos", "macos-arm64"],
        "automated": True,
    },
    {
        "id": "pongo_test",
        "name": "Test Emulator",
        "description": "Verify QEMU can boot pongoOS",
        "platforms": ["windows", "linux", "macos", "macos-arm64"],
        "automated": True,
    },
]


def _script_install_deps(platform, work_dir):
    """Install build dependencies for UTMapp QEMU and pongoOS."""
    if is_macos(platform):
        arch_note = "ARM64 (Apple Silicon)" if platform == "macos-arm64" else "x86_64 (Intel)"
        return f'''
echo "SS_INFO:Detected macOS {arch_note}"
echo "SS_INFO:Installing build dependencies via Homebrew..."
brew install ninja meson glib pixman || exit 1
echo "SS_INFO:Dependencies installed successfully"
'''
    # linux / windows (WSL)
    return '''
echo "SS_INFO:Checking sudo access..."
if ! sudo -n true 2>/dev/null; then
    echo "SS_ERROR:sudo requires a password. Set up passwordless sudo first."
    exit 1
fi
echo "SS_INFO:Installing QEMU build dependencies via apt..."
sudo -n apt-get update || exit 1
sudo -n apt-get install -y ninja-build meson pkg-config python3 \
    libglib2.0-dev libpixman-1-dev libfdt-dev zlib1g-dev \
    automake make autoconf git wget tar xz-utils lzma xxd || exit 1
echo "SS_INFO:Dependencies installed successfully"
'''


def _script_build_utm_qemu(platform, work_dir):
    """Build UTMapp QEMU with pongoOS memory patch (all platforms)."""
    return f'''
cd "{work_dir}" || exit 1
QEMU_DIR="{work_dir}/utm-qemu"
QEMU_BUILD="{work_dir}/utm-qemu-build"

# Clone UTMapp QEMU if not exists
if [ -d "$QEMU_DIR/.git" ]; then
    echo "SS_INFO:UTMapp QEMU already cloned, pulling latest..."
    cd "$QEMU_DIR" || exit 1
    git pull || exit 1
else
    echo "SS_INFO:Cloning UTMapp QEMU (this may take a few minutes)..."
    git clone --depth 1 https://github.com/utmapp/qemu.git "$QEMU_DIR" || exit 1
    cd "$QEMU_DIR" || exit 1
fi

# Apply pongoOS memory patch
echo "SS_INFO:Applying pongoOS memory layout patch..."
VIRT_C="hw/arm/virt.c"
if ! grep -q "0x800000000" "$VIRT_C" 2>/dev/null; then
    echo "SS_INFO:Patching $VIRT_C..."
    # Backup original
    cp "$VIRT_C" "$VIRT_C.bak" 2>/dev/null || true
    # Apply patch: change [VIRT_MEM] = {{ GiB, to {{ 0x800000000,
    sed -i 's/\\[VIRT_MEM\\][[:space:]]*=[[:space:]]*{{[[:space:]]*GiB,/[VIRT_MEM] = {{ 0x800000000,/g' "$VIRT_C" || exit 1
    echo "SS_INFO:Patch applied successfully"
else
    echo "SS_INFO:Patch already applied"
fi

# Configure QEMU build (minimal targets for pongoOS)
echo "SS_INFO:Configuring QEMU build (aarch64 target only)..."
cd "$QEMU_DIR" || exit 1

# Clean any stale build files to avoid meson version conflicts
echo "SS_INFO:Cleaning previous build artifacts..."
make distclean 2>/dev/null || true

"$QEMU_DIR/configure" \
    --prefix=/opt/utm-qemu \
    --target-list=aarch64-softmmu \
    --enable-tcg \
    --disable-docs \
    --disable-werror || exit 1

# Build QEMU (use all CPU cores)
echo "SS_INFO:Building QEMU (this may take 10-15 minutes)..."
echo "SS_INFO:Using $(nproc 2>/dev/null || echo 4) CPU cores..."
make -j$(nproc 2>/dev/null || echo 4) || exit 1

# Install to /opt/utm-qemu
echo "SS_INFO:Installing QEMU to /opt/utm-qemu..."
sudo -n make install || exit 1

# Verify installation
if [ -f "/opt/utm-qemu/bin/qemu-system-aarch64" ]; then
    echo "SS_INFO:UTMapp QEMU installed successfully"
    /opt/utm-qemu/bin/qemu-system-aarch64 --version | head -1
else
    echo "SS_ERROR:QEMU binary not found after install"
    exit 1
fi
'''


def _script_setup_toolchain(platform, work_dir):
    """Install clang, ld64, and cctools-strip from checkra1n repo (Linux/WSL only)."""
    return f'''
echo "SS_INFO:Setting up cross-compilation toolchain (official checkra1n method)..."

# Check if ld64 and cctools-strip are already installed
if command -v ld64 >/dev/null 2>&1 && command -v cctools-strip >/dev/null 2>&1 && command -v clang >/dev/null 2>&1; then
    echo "SS_INFO:All tools already installed"
    echo "SS_INFO:clang: $(clang --version 2>&1 | head -1)"
    echo "SS_INFO:ld64: $(which ld64)"
    echo "SS_INFO:cctools-strip: $(which cctools-strip)"
    echo "SS_INFO:Toolchain setup complete"
    exit 0
fi

# Add checkra1n Debian repo for ld64 and cctools-strip
echo "SS_INFO:Adding checkra1n Debian repository..."
if [ ! -f /etc/apt/sources.list.d/checkra1n.list ]; then
    echo "{CHECKRA1N_REPO_LINE}" > /tmp/checkra1n.list
    sudo -n cp /tmp/checkra1n.list /etc/apt/sources.list.d/checkra1n.list || exit 1
    rm -f /tmp/checkra1n.list
    echo "SS_INFO:Importing checkra1n GPG key..."
    sudo -n apt-key adv --fetch-keys {CHECKRA1N_KEY_URL} || exit 1
else
    echo "SS_INFO:checkra1n repo already configured"
fi

echo "SS_INFO:Updating package lists..."
sudo -n apt-get update || exit 1

# Install ld64 and cctools-strip from checkra1n repo
echo "SS_INFO:Installing ld64 and cctools-strip..."
sudo -n apt-get install -y ld64 cctools-strip || exit 1

# Install system clang
echo "SS_INFO:Installing clang..."
sudo -n apt-get install -y clang || exit 1

# Verify all tools
echo "SS_INFO:Verifying toolchain..."
if ! command -v clang >/dev/null 2>&1; then
    echo "SS_ERROR:clang not found after install"
    exit 1
fi
if ! command -v ld64 >/dev/null 2>&1; then
    echo "SS_ERROR:ld64 not found after install"
    exit 1
fi
if ! command -v cctools-strip >/dev/null 2>&1; then
    echo "SS_ERROR:cctools-strip not found after install"
    exit 1
fi
echo "SS_INFO:clang: $(clang --version 2>&1 | head -1)"
echo "SS_INFO:ld64: $(which ld64)"
echo "SS_INFO:cctools-strip: $(which cctools-strip)"
echo "SS_INFO:Toolchain setup complete"
'''


def _script_download_pongoos(platform, work_dir):
    """Clone pongoOS-QEMU and build from source."""
    # Common clone step
    clone_block = f'''
cd "{work_dir}" || exit 1
echo "SS_INFO:Cloning pongoOS-QEMU repository..."
echo "SS_INFO:Using karamzaki/pongoOS-QEMU fork (optimized for QEMU)"
if [ -d "pongoOS-src/.git" ]; then
    echo "SS_INFO:pongoOS repo exists, pulling latest..."
    cd pongoOS-src || exit 1
    git pull || exit 1
    cd "{work_dir}" || exit 1
else
    git clone --depth 1 {PONGOOS_REPO} pongoOS-src || exit 1
fi
cd "{work_dir}/pongoOS-src" || exit 1
'''
    # Patch source for Linux cross-compilation compatibility
    patch_source = '''
echo "SS_INFO:Patching Makefiles for Linux cross-compilation..."
find . -name "Makefile" -o -name "*.mk" | while read mf; do
    sed -i.bak 's/-Werror//g; s/-flto//g; s/-Wl,-fatal_warnings//g' "$mf" 2>/dev/null || true
done
echo "SS_INFO:Patching missing includes for Linux cross-compilation..."
grep -rl 'va_start' --include='*.c' . 2>/dev/null | while read f; do
    if ! grep -q '#include <stdarg.h>' "$f"; then
        sed -i '1i #include <stdarg.h>' "$f"
        echo "SS_INFO:  Added stdarg.h to $f"
    fi
done
'''
    # Verify and copy output
    verify_block = f'''
echo "SS_INFO:Verifying build output..."
if [ -f "build/pongoOS" ]; then
    echo "SS_INFO:Copying pongoOS binary..."
    cp build/pongoOS "{work_dir}/pongoOS" || exit 1
elif [ -f "build/Pongo.bin" ]; then
    echo "SS_INFO:Copying Pongo.bin binary..."
    cp build/Pongo.bin "{work_dir}/pongoOS" || exit 1
elif [ -f "build/Pongo" ]; then
    echo "SS_INFO:Found Pongo Mach-O, converting to flat binary..."
    if [ -f "build/vmacho" ]; then
        ./build/vmacho -f build/Pongo "{work_dir}/pongoOS" || exit 1
    elif command -v cc >/dev/null 2>&1; then
        cc -Wall -O3 -o build/vmacho tools/vmacho.c || exit 1
        ./build/vmacho -f build/Pongo "{work_dir}/pongoOS" || exit 1
    else
        echo "SS_ERROR:Found Pongo Mach-O but no compiler to build vmacho converter"
        exit 1
    fi
else
    echo "SS_ERROR:No pongoOS binary found after build"
    echo "SS_INFO:Expected one of: build/pongoOS, build/Pongo.bin, build/Pongo"
    ls -la build/ 2>/dev/null || true
    exit 1
fi

echo "SS_INFO:pongoOS built successfully"
ls -lh "{work_dir}/pongoOS"
'''

    if is_macos(platform):
        # macOS: build natively with Xcode toolchain
        return clone_block + patch_source + '''
echo "SS_INFO:Building pongoOS with Xcode toolchain..."
xcode-select --install 2>/dev/null || true
make clean || true
make || exit 1
''' + verify_block

    # Linux / Windows (WSL): build with system clang + ld64 + cctools-strip
    # (official checkra1n build method)
    return clone_block + patch_source + '''
# Verify cross-compilation tools are installed
if ! command -v clang >/dev/null 2>&1; then
    echo "SS_ERROR:clang not found. Run the Setup Toolchain step first."
    exit 1
fi
if ! command -v ld64 >/dev/null 2>&1; then
    echo "SS_ERROR:ld64 not found. Run the Setup Toolchain step first."
    exit 1
fi
if ! command -v cctools-strip >/dev/null 2>&1; then
    echo "SS_ERROR:cctools-strip not found. Run the Setup Toolchain step first."
    exit 1
fi

echo "SS_INFO:Using system clang + ld64 + cctools-strip (official method)"
echo "SS_INFO:clang: $(clang --version 2>&1 | head -1)"

echo "SS_INFO:Building pongoOS..."
make clean || true
EMBEDDED_CC="clang -target arm64-apple-ios12.0.0 -fuse-ld=/usr/bin/ld64 -fcommon" STRIP=cctools-strip make all || exit 1
''' + verify_block


def _script_test_pongoos(platform, work_dir):
    """Test that QEMU can boot pongoOS."""
    return f'''
cd "{work_dir}" || exit 1
echo "SS_INFO:Testing pongoOS boot..."
if [ ! -f "pongoOS" ]; then
    echo "SS_ERROR:pongoOS binary not found at {work_dir}/pongoOS"
    exit 1
fi
if [ ! -f "/opt/utm-qemu/bin/qemu-system-aarch64" ]; then
    echo "SS_ERROR:UTMapp QEMU not found. Run 'Build UTMapp QEMU' step first."
    exit 1
fi
echo "SS_INFO:Starting QEMU test (will timeout after 5 seconds)..."
echo "SS_INFO:Using UTMapp QEMU with pongoOS loader method..."
timeout 5 /opt/utm-qemu/bin/qemu-system-aarch64 \
    -M virt -cpu cortex-a72 -accel tcg -m 4096 \
    -device loader,file=pongoOS,addr=0x1000,force-raw=on \
    -device loader,addr=0x1000,cpu-num=0 \
    -nographic </dev/null || true
echo "SS_INFO:pongoOS test completed"
echo "SS_INFO:Setup complete! Use Launch Emulator to start pongoOS."
'''


def get_script_for_step(step_id, platform, work_dir):
    """
    Get bash script for a pongoOS setup step.

    Args:
        step_id: Step identifier
        platform: "windows", "macos", or "linux"
        work_dir: Working directory path

    Returns:
        Bash script string, or None for manual steps
    """
    scripts = {
        "pongo_deps": _script_install_deps,
        "pongo_qemu": _script_build_utm_qemu,
        "pongo_toolchain": _script_setup_toolchain,
        "pongo_download": _script_download_pongoos,
        "pongo_test": _script_test_pongoos,
    }

    script_fn = scripts.get(step_id)
    if script_fn:
        return script_fn(platform, work_dir)

    return None


def get_step_info(step_id):
    """
    Get step information.

    Args:
        step_id: Step identifier

    Returns:
        Step dict or None
    """
    for step in PONGOOS_STEPS:
        if step["id"] == step_id:
            return step
    return None


def get_steps_for_platform(platform):
    """
    Get all steps for a specific platform.

    Args:
        platform: "windows", "macos", or "linux"

    Returns:
        List of step dicts
    """
    return [s for s in PONGOOS_STEPS if platform in s["platforms"]]
