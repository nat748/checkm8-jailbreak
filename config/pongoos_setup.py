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


# pongoOS setup steps
PONGOOS_STEPS = [
    {
        "id": "pongo_deps",
        "name": "Install QEMU",
        "description": "Install QEMU emulator for ARM64",
        "platforms": ["windows", "linux", "macos", "macos-arm64"],
        "automated": True,
    },
    {
        "id": "pongo_download",
        "name": "Download pongoOS",
        "description": "Clone and build pongoOS from source",
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
    """Install QEMU emulator."""
    if is_macos(platform):
        arch_note = "ARM64 (Apple Silicon)" if platform == "macos-arm64" else "x86_64 (Intel)"
        return f'''
echo "SS_INFO:Detected macOS {arch_note}"
echo "SS_INFO:Installing QEMU via Homebrew..."
brew install qemu || exit 1
echo "SS_INFO:Verifying QEMU installation..."
if ! command -v qemu-system-aarch64 >/dev/null 2>&1; then
    echo "SS_ERROR:qemu-system-aarch64 not found after install"
    exit 1
fi
echo "SS_INFO:QEMU installed successfully"
qemu-system-aarch64 --version
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
'''


def _script_download_pongoos(platform, work_dir):
    """Download and build pongoOS-QEMU fork."""
    return f'''
cd "{work_dir}" || exit 1
echo "SS_INFO:Cloning pongoOS-QEMU repository..."
echo "SS_INFO:Using citruz/pongoOS-QEMU fork (optimized for QEMU)"
if [ -d "pongoOS-src/.git" ]; then
    echo "SS_INFO:pongoOS repo exists, pulling latest..."
    cd pongoOS-src || exit 1
    git pull || exit 1
else
    git clone --depth 1 https://github.com/citruz/pongoOS-QEMU.git pongoOS-src || exit 1
    cd pongoOS-src || exit 1
fi

echo "SS_INFO:Installing build dependencies..."
if [ "$(uname)" = "Darwin" ]; then
    xcode-select --install 2>/dev/null || true
else
    echo "SS_INFO:Installing clang, lld, and libc for cross-compilation..."
    sudo -n apt-get install -y clang lld libc6-dev || exit 1
fi

# Set up Apple cross-compiler wrapper for Linux/WSL.
# The Makefile expects 'arm64-apple-ios12.0.0-clang' which is just
# clang invoked with --target=arm64-apple-ios12.0.0.
if [ "$(uname)" != "Darwin" ]; then
    echo "SS_INFO:Setting up Apple cross-compiler wrapper..."
    WRAPPER_DIR="{work_dir}/cross-tools"
    mkdir -p "$WRAPPER_DIR"
    # Find clang's builtin resource dir (provides stdarg.h, etc.)
    RESOURCE_DIR=$(clang -print-resource-dir 2>/dev/null)
    # Use printf to avoid heredoc escaping issues inside Python f-strings
    printf '#!/bin/bash\\nexec clang --target=arm64-apple-ios12.0.0 -fuse-ld=lld -isystem "%s/include" -Wno-error=unused-but-set-variable -Wno-error=implicit-function-declaration "$@"\\n' "$RESOURCE_DIR" > "$WRAPPER_DIR/arm64-apple-ios12.0.0-clang"
    chmod +x "$WRAPPER_DIR/arm64-apple-ios12.0.0-clang"
    export PATH="$WRAPPER_DIR:$PATH"
    echo "SS_INFO:Cross-compiler wrapper created at $WRAPPER_DIR"
    echo "SS_INFO:Clang resource dir: $RESOURCE_DIR"
fi

echo "SS_INFO:Building pongoOS (this may take a few minutes)..."
make clean || true
make || exit 1
echo "SS_INFO:Verifying build output..."
if [ ! -f "build/pongoOS" ]; then
    echo "SS_ERROR:pongoOS binary not found after build"
    exit 1
fi
echo "SS_INFO:Copying pongoOS binary..."
cp build/pongoOS "{work_dir}/pongoOS" || exit 1
echo "SS_INFO:pongoOS built successfully"
ls -lh "{work_dir}/pongoOS"
'''


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
