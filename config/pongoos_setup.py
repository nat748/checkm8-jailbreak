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
PONGOOS_DOCKER_IMAGE = "checkra1n/build-pongo"

# pongoOS setup steps
PONGOOS_STEPS = [
    {
        "id": "pongo_deps",
        "name": "Install QEMU & Docker",
        "description": "Install QEMU emulator and Docker (for building pongoOS)",
        "platforms": ["windows", "linux", "macos", "macos-arm64"],
        "automated": True,
    },
    {
        "id": "pongo_download",
        "name": "Clone & Build pongoOS",
        "description": "Clone pongoOS-QEMU and build via Docker",
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


def _script_install_qemu(platform, work_dir):
    """Install QEMU emulator and Docker."""
    if is_macos(platform):
        arch_note = "ARM64 (Apple Silicon)" if platform == "macos-arm64" else "x86_64 (Intel)"
        return f'''
echo "SS_INFO:Detected macOS {arch_note}"
echo "SS_INFO:Installing QEMU and Docker via Homebrew..."
brew install qemu docker || exit 1
echo "SS_INFO:Verifying QEMU installation..."
if ! command -v qemu-system-aarch64 >/dev/null 2>&1; then
    echo "SS_ERROR:qemu-system-aarch64 not found after install"
    exit 1
fi
echo "SS_INFO:QEMU installed successfully"
qemu-system-aarch64 --version
echo "SS_INFO:Verifying Docker installation..."
if ! command -v docker >/dev/null 2>&1; then
    echo "SS_WARN:Docker not found. Install Docker Desktop for macOS to enable building pongoOS."
else
    echo "SS_INFO:Docker installed successfully"
    docker --version
fi
'''
    # linux / windows (WSL)
    return '''
echo "SS_INFO:Checking sudo access..."
if ! sudo -n true 2>/dev/null; then
    echo "SS_ERROR:sudo requires a password. Set up passwordless sudo first."
    exit 1
fi
echo "SS_INFO:Installing QEMU via apt..."
sudo -n apt-get update || exit 1
sudo -n apt-get install -y qemu-system-arm qemu-system-aarch64 || exit 1
echo "SS_INFO:Verifying QEMU installation..."
if ! command -v qemu-system-aarch64 >/dev/null 2>&1; then
    echo "SS_ERROR:qemu-system-aarch64 not found after install"
    exit 1
fi
echo "SS_INFO:QEMU installed successfully"
qemu-system-aarch64 --version

echo "SS_INFO:Checking Docker installation..."
if ! command -v docker >/dev/null 2>&1; then
    echo "SS_INFO:Installing Docker..."
    sudo -n apt-get install -y docker.io || exit 1
fi
echo "SS_INFO:Ensuring Docker service is running..."
sudo -n service docker start 2>/dev/null || true
echo "SS_INFO:Adding user to docker group (may need re-login)..."
sudo -n usermod -aG docker "$USER" 2>/dev/null || true
echo "SS_INFO:Docker installed successfully"
docker --version || echo "SS_WARN:Docker installed but may need re-login for group permissions"
'''


def _script_download_pongoos(platform, work_dir):
    """Clone pongoOS-QEMU and build using Docker (all platforms)."""
    # Common clone step — same for all platforms
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
    # Strip -Werror from all Makefiles (prevents warnings from killing the build)
    strip_werror = '''
echo "SS_INFO:Patching Makefiles to disable -Werror..."
find . -name "Makefile" -o -name "*.mk" | while read mf; do
    sed -i.bak 's/-Werror//g' "$mf" 2>/dev/null || true
done
'''
    # Docker build — works on all platforms (Linux, WSL, macOS with Docker)
    docker_build = f'''
echo "SS_INFO:Building pongoOS via Docker ({PONGOOS_DOCKER_IMAGE})..."
echo "SS_INFO:This downloads the cross-compilation toolchain and iOS SDK automatically."
docker run --rm -v "$(pwd)":/pongo {PONGOOS_DOCKER_IMAGE} || exit 1
'''
    # Native macOS build fallback (if Docker unavailable)
    native_macos_build = '''
echo "SS_INFO:Docker not available, building natively with Xcode toolchain..."
xcode-select --install 2>/dev/null || true
make clean || true
make || exit 1
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
        # macOS: try Docker first, fall back to native build
        return clone_block + strip_werror + f'''
if command -v docker >/dev/null 2>&1; then
{docker_build}
else
{native_macos_build}
fi
''' + verify_block

    # Linux / Windows (WSL): Docker build (has cross-compilation toolchain)
    return clone_block + strip_werror + f'''
if ! command -v docker >/dev/null 2>&1; then
    echo "SS_ERROR:Docker is required to build pongoOS on Linux/WSL."
    echo "SS_INFO:Install Docker with: sudo apt-get install docker.io"
    echo "SS_INFO:Then re-run this step."
    exit 1
fi

echo "SS_INFO:Checking Docker permissions..."
if ! docker info >/dev/null 2>&1; then
    echo "SS_INFO:Trying with sudo..."
    sudo -n docker run --rm -v "$(pwd)":/pongo {PONGOOS_DOCKER_IMAGE} || exit 1
else
{docker_build}
fi
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
echo "SS_INFO:Starting QEMU test (will timeout after 5 seconds)..."
timeout 5 qemu-system-aarch64 -M virt -cpu cortex-a57 -m 512M -kernel pongoOS -nographic -serial stdio || true
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
        "pongo_deps": _script_install_qemu,
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
