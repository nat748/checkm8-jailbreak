"""
Inferno emulator setup step definitions.

Each step has an id, display info, platform support, and a function
that returns the bash script to execute.  Manual steps return None
and provide instruction text instead.
"""

import sys

# iOS 14.0 beta 5 for iPhone 12,1 (iPhone 11)
IPSW_URL = (
    "https://updates.cdn-apple.com/2020SummerSeed/fullrestores/"
    "001-35886/5FE9BE2E-17F8-41C8-96BB-B76E2B225888/"
    "iPhone11,8,iPhone12,1_14.0_18A5351d_Restore.ipsw"
)
IPSW_FILENAME = "iPhone11,8,iPhone12,1_14.0_18A5351d_Restore.ipsw"


def detect_platform():
    """Return 'windows', 'macos', or 'linux'."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


# ── Script generators ──────────────────────────────────────────────
# Each returns a bash script string with SS_STEP / SS_INFO / SS_ERROR
# prefixes for progress parsing.  The work_dir argument is the
# absolute path where all Inferno files live (inside WSL on Windows).

def _script_install_deps(platform, work_dir):
    if platform == "macos":
        return '''
SS_INFO:Checking for Homebrew...
if ! command -v brew >/dev/null 2>&1; then
    SS_ERROR:Homebrew not found. Install from https://brew.sh first.
    exit 1
fi
SS_INFO:Installing dependencies via Homebrew...
brew install libtool meson ninja pkgconf capstone dtc glib gnutls \\
    jpeg-turbo libpng libslirp libssh libusb lzo ncurses pixman \\
    snappy vde zstd libtasn1
SS_INFO:Dependencies installed
'''
    # linux / windows (WSL Ubuntu)
    return '''
SS_INFO:Checking sudo access...
if ! sudo -n true 2>/dev/null; then
    SS_ERROR:sudo requires a password. Set up passwordless sudo first:
    SS_INFO:  echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER
    exit 1
fi
SS_INFO:Updating package lists...
sudo -n apt-get update
SS_INFO:Installing build dependencies...
sudo -n apt-get install -y \\
    build-essential git libtool meson ninja-build pkg-config \\
    libcapstone-dev device-tree-compiler libglib2.0-dev gnutls-bin \\
    libjpeg-dev libpng-dev libslirp-dev libssh-dev \\
    libusb-1.0-0-dev liblzo2-dev libncurses-dev libpixman-1-dev \\
    libsnappy-dev vde2 zstd libgnutls28-dev \\
    libgtk-3-dev libsdl2-dev
SS_INFO:Building lzfse from source...
if [ ! -d "/tmp/lzfse" ]; then
    cd /tmp
    git clone https://github.com/lzfse/lzfse
    cd lzfse
    mkdir -p build && cd build
    cmake .. && make
    sudo make install
    sudo ldconfig
fi
SS_INFO:Dependencies installed
'''


def _script_clone_inferno(platform, work_dir):
    return f'''
cd "{work_dir}" || exit 1
if [ -d "Inferno/.git" ]; then
    SS_INFO:Inferno repo already exists, updating...
    cd Inferno || exit 1
    git pull
    git submodule update --init
else
    SS_INFO:Cloning Inferno repository...
    git clone https://github.com/ChefKissInc/Inferno
    cd Inferno || exit 1
    SS_INFO:Initializing submodules...
    git submodule update --init
fi
SS_INFO:Inferno repository ready
'''


def _script_build_inferno(platform, work_dir):
    if platform == "macos":
        # Detect arm64 vs x86_64
        return f'''
cd "{work_dir}/Inferno" || exit 1
mkdir -p build && cd build || exit 1
SS_INFO:Configuring Inferno build for macOS...
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    SS_INFO:Detected Apple Silicon (arm64)
    LIBTOOL="glibtool" ../configure \\
        --target-list=aarch64-softmmu,x86_64-softmmu \\
        --disable-bsd-user --disable-guest-agent \\
        --enable-lzfse --enable-slirp --enable-capstone --enable-curses \\
        --enable-libssh --enable-virtfs --enable-zstd \\
        --extra-cflags=-DNCURSES_WIDECHAR=1 \\
        --disable-sdl --disable-gtk --enable-cocoa \\
        --enable-nettle --enable-gnutls \\
        --extra-cflags="-I/opt/homebrew/include -O3 -ffast-math -mtune=native" \\
        --extra-ldflags="-L/opt/homebrew/lib" \\
        --disable-werror --disable-tests --disable-qom-cast-debug --disable-plugins
else
    SS_INFO:Detected Intel (x86_64)
    LIBTOOL="glibtool" ../configure \\
        --target-list=aarch64-softmmu,x86_64-softmmu \\
        --disable-bsd-user --disable-guest-agent \\
        --enable-lzfse --enable-slirp --enable-capstone --enable-curses \\
        --enable-libssh --enable-virtfs --enable-zstd \\
        --extra-cflags=-DNCURSES_WIDECHAR=1 \\
        --disable-sdl --disable-gtk --enable-cocoa \\
        --enable-nettle --enable-gnutls \\
        --disable-werror --disable-tests --disable-qom-cast-debug --disable-plugins \\
        --extra-cflags="-O3 -ffast-math -mtune=native"
fi
SS_INFO:Building Inferno (this may take 10-20 minutes)...
make -j$(sysctl -n hw.logicalcpu)
SS_INFO:Inferno built successfully
'''
    # linux / windows WSL
    return f'''
cd "{work_dir}/Inferno" || exit 1
mkdir -p build && cd build || exit 1
SS_INFO:Configuring Inferno build for Linux...
../configure \\
    --target-list=aarch64-softmmu,x86_64-softmmu \\
    --enable-lzfse --enable-slirp --enable-capstone --enable-curses \\
    --enable-libssh --enable-virtfs --enable-zstd \\
    --enable-nettle --enable-gnutls --enable-gtk --enable-sdl \\
    --disable-werror --disable-tests --disable-qom-cast-debug --disable-plugins \\
    --extra-cflags="-O3 -ffast-math"
SS_INFO:Building Inferno (this may take 10-20 minutes)...
make -j$(nproc)
SS_INFO:Inferno built successfully
'''


def _script_create_disks(platform, work_dir):
    return f'''
cd "{work_dir}" || exit 1
QIMG="./Inferno/build/qemu-img"
if [ ! -f "$QIMG" ]; then
    SS_ERROR:qemu-img not found. Build Inferno first (step 3).
    exit 1
fi
SS_INFO:Creating disk images (this may take a minute)...
"$QIMG" create -f raw root 32G
"$QIMG" create -f raw firmware 8M
"$QIMG" create -f raw syscfg 128K
"$QIMG" create -f raw ctrl_bits 8K
"$QIMG" create -f raw nvram 8K
"$QIMG" create -f raw effaceable 4K
"$QIMG" create -f raw panic_log 1M
"$QIMG" create -f raw sep_nvram 64K
"$QIMG" create -f raw sep_ssc 128K
SS_INFO:All 9 disk images created successfully
'''


def _script_download_ipsw(platform, work_dir):
    return f'''
cd "{work_dir}" || exit 1
IPSW="{IPSW_FILENAME}"
if [ -f "$IPSW" ]; then
    SIZE=$(stat -f%z "$IPSW" 2>/dev/null || stat -c%s "$IPSW" 2>/dev/null)
    if [ "$SIZE" -gt 5000000000 ]; then
        SS_INFO:IPSW already downloaded ($SIZE bytes), skipping.
        exit 0
    else
        SS_INFO:Existing IPSW is incomplete, redownloading...
        rm -f "$IPSW"
    fi
fi
SS_INFO:Downloading iOS 14.0 beta 5 firmware (~5.4 GB)...
SS_INFO:This will take 10-30 minutes depending on your connection.
curl -L -o "$IPSW" --progress-bar "{IPSW_URL}"
if [ ! -f "$IPSW" ]; then
    SS_ERROR:Download failed.
    exit 1
fi
SIZE=$(stat -f%z "$IPSW" 2>/dev/null || stat -c%s "$IPSW" 2>/dev/null)
SS_INFO:Downloaded $SIZE bytes
SS_INFO:IPSW download complete
'''


def _script_extract_ipsw(platform, work_dir):
    return f'''
cd "{work_dir}" || exit 1
IPSW="{IPSW_FILENAME}"
if [ ! -f "$IPSW" ]; then
    SS_ERROR:IPSW not found. Download it first (step 5).
    exit 1
fi
if [ -d "Restore" ] && [ -f "Restore/BuildManifest.plist" ]; then
    SS_INFO:Restore directory already exists with valid content, skipping extraction.
    exit 0
fi
SS_INFO:Extracting IPSW (this may take 2-5 minutes)...
rm -rf Restore
unzip -q "$IPSW" -d Restore
if [ ! -f "Restore/BuildManifest.plist" ]; then
    SS_ERROR:Extraction failed or incomplete.
    exit 1
fi
SS_INFO:Firmware extracted to Restore/
'''


def _script_generate_tickets(platform, work_dir):
    return f'''
cd "{work_dir}" || exit 1
SCRIPTS="./Inferno/Extras/Inferno"
if [ ! -d "$SCRIPTS" ]; then
    SCRIPTS="./Inferno/extras/Inferno"
fi
if [ ! -d "$SCRIPTS" ]; then
    SS_ERROR:Ticket scripts not found in Inferno repo.
    SS_INFO:Expected location: Inferno/Extras/Inferno/
    exit 1
fi

SS_INFO:Setting up Python environment...
if [ ! -d "inferno_tools_venv" ]; then
    python3 -m venv inferno_tools_venv || python -m venv inferno_tools_venv
fi
. inferno_tools_venv/bin/activate
pip install -q pyasn1 pyasn1-modules

TICKET="$SCRIPTS/ticket.shsh2"
if [ ! -f "$TICKET" ]; then
    SS_ERROR:ticket.shsh2 not found in $SCRIPTS
    exit 1
fi

if [ ! -f "./Restore/BuildManifest.plist" ]; then
    SS_ERROR:BuildManifest.plist not found. Extract IPSW first (step 6).
    exit 1
fi

SS_INFO:Generating AP ticket...
python3 "$SCRIPTS/create_apticket.py" n104ap ./Restore/BuildManifest.plist "$TICKET" ./root_ticket.der
if [ ! -f "root_ticket.der" ]; then
    SS_ERROR:AP ticket generation failed
    exit 1
fi
SS_INFO:Created root_ticket.der

SS_INFO:Generating SEP ticket...
python3 "$SCRIPTS/create_septicket.py" n104ap ./Restore/BuildManifest.plist "$TICKET" ./sep_root_ticket.der
if [ ! -f "sep_root_ticket.der" ]; then
    SS_ERROR:SEP ticket generation failed
    exit 1
fi
SS_INFO:Created sep_root_ticket.der
SS_INFO:Tickets generated successfully
'''


def _script_build_img4lib(platform, work_dir):
    if platform == "macos":
        return f'''
cd "{work_dir}" || exit 1
if [ -f "img4lib/img4" ]; then
    SS_INFO:img4lib already built, skipping.
    exit 0
fi
SS_INFO:Cloning img4lib...
git clone https://github.com/xerub/img4lib
cd img4lib || exit 1
SS_INFO:Building img4lib...
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    make LDFLAGS="-L/opt/homebrew/opt/openssl/lib -L/opt/homebrew/opt/lzfse/lib" \\
         CFLAGS="-I/opt/homebrew/opt/openssl/include -I/opt/homebrew/opt/lzfse/include -Wall -W -pedantic -Wno-variadic-macros -Wno-multichar -Wno-four-char-constants -Wno-unused-parameter -O2 -I. -g -DiOS10 -DDER_MULTIBYTE_TAGS=1 -DER_TAG_SIZE=8"
else
    make LDFLAGS="-L/usr/local/opt/openssl/lib -L/usr/local/opt/lzfse/lib" \\
         CFLAGS="-I/usr/local/opt/openssl/include -I/usr/local/opt/lzfse/include -Wall -W -pedantic -Wno-variadic-macros -Wno-multichar -Wno-four-char-constants -Wno-unused-parameter -O2 -I. -g -DiOS10 -DDER_MULTIBYTE_TAGS=1 -DER_TAG_SIZE=8"
fi
SS_INFO:img4lib built successfully
'''
    # linux / WSL
    return f'''
cd "{work_dir}" || exit 1
if [ -f "img4lib/img4" ]; then
    SS_INFO:img4lib already built, skipping.
    exit 0
fi
SS_INFO:Cloning img4lib...
git clone https://github.com/xerub/img4lib
cd img4lib || exit 1
SS_INFO:Installing build dependencies...
sudo -n apt-get install -y libssl-dev
SS_INFO:Building img4lib...
make
SS_INFO:img4lib built successfully
'''


def _script_fs_patches(platform, work_dir):
    """macOS only — filesystem patches using hdiutil."""
    if platform != "macos":
        return None
    return f'''
cd "{work_dir}" || exit 1
if [ ! -f "root" ]; then
    SS_ERROR:Root disk image not found. Create disk images first (step 4).
    exit 1
fi
SS_INFO:Attaching root disk image...
hdiutil attach -imagekey diskimage-class=CRawDiskImage -blocksize 4096 -noverify -noautofsck root

SS_INFO:Enabling ownership and read-write mount...
sudo diskutil enableownership /Volumes/System
sudo mount -urw /Volumes/System

if [ ! -d "InfernoFSPatcher" ]; then
    SS_INFO:Cloning InfernoFSPatcher...
    git clone https://git.chefkiss.dev/AppleHax/InfernoFSPatcher
fi
cd InfernoFSPatcher || exit 1
SS_INFO:Building patcher...
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

SS_INFO:Patching dyld shared cache...
sudo build/inferno_fs_patcher /Volumes/System/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64e

SS_INFO:Ejecting disk...
diskutil eject /Volumes/System
SS_INFO:Filesystem patches applied successfully
'''


# ── Step definitions ───────────────────────────────────────────────

SETUP_STEPS = [
    {
        "id": "install_deps",
        "name": "Install Dependencies",
        "description": "Install build tools and libraries required to compile Inferno.",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_install_deps,
    },
    {
        "id": "clone_inferno",
        "name": "Clone Inferno",
        "description": "Clone the Inferno QEMU fork and initialize submodules.",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_clone_inferno,
    },
    {
        "id": "build_inferno",
        "name": "Build Inferno",
        "description": "Configure and compile Inferno from source. This may take 10-20 minutes.",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_build_inferno,
    },
    {
        "id": "create_disks",
        "name": "Create Disk Images",
        "description": "Create the 9 raw disk images required by the emulator.",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_create_disks,
    },
    {
        "id": "download_ipsw",
        "name": "Download iOS Firmware",
        "description": "Download the iOS 14.0 beta 5 IPSW from Apple (~5.4 GB).",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_download_ipsw,
    },
    {
        "id": "extract_ipsw",
        "name": "Extract Firmware",
        "description": "Extract the downloaded IPSW archive.",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_extract_ipsw,
    },
    {
        "id": "generate_tickets",
        "name": "Generate Tickets",
        "description": "Generate AP and SEP tickets using scripts from the Inferno repo.",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_generate_tickets,
    },
    {
        "id": "build_img4lib",
        "name": "Build img4lib",
        "description": "Clone and build img4lib (needed for SEP firmware processing).",
        "platforms": ["windows", "linux", "macos"],
        "automated": True,
        "script_fn": _script_build_img4lib,
    },
    {
        "id": "extract_sep",
        "name": "Extract SEP Firmware",
        "description": "Extract and re-sign SEP firmware using img4lib.",
        "platforms": ["windows", "linux", "macos"],
        "automated": False,
        "manual_instructions": (
            "This step requires SEP encryption keys that cannot be distributed.\n\n"
            "Run the following command with the correct IV+KEY:\n\n"
            "  cd <work_dir>\n"
            "  ./img4lib/img4 -i ./Restore/Firmware/all_flash/"
            "sep-firmware.n104.RELEASE.im4p \\\n"
            "    -o ./sep-firmware.n104.RELEASE.new.img4 \\\n"
            "    -M ./sep_root_ticket.der -T rsep\n\n"
            "Refer to the Inferno guide for details on obtaining keys:\n"
            "https://chefkiss.dev/guides/inferno/file-setup/"
        ),
    },
    {
        "id": "companion_vm",
        "name": "Setup Companion VM",
        "description": "Set up a lightweight Linux VM for iOS restore and USB bridging.",
        "platforms": ["windows", "linux", "macos"],
        "automated": False,
        "manual_instructions": (
            "A companion VM (Arch or Artix Linux) is needed to run\n"
            "idevicerestore and provide USB connectivity.\n\n"
            "Inside the companion VM, build from source:\n"
            "  libplist, libtatsu, libimobiledevice-glue,\n"
            "  libusbmuxd, libirecovery, libimobiledevice,\n"
            "  usbmuxd, idevicerestore\n\n"
            "Apply the patch from Inferno/Extras/Inferno/idevicerestore.patch\n"
            "before building idevicerestore.\n\n"
            "Full guide: https://chefkiss.dev/guides/inferno/companion-setup/"
        ),
    },
    {
        "id": "restore_ios",
        "name": "Restore iOS",
        "description": "Run idevicerestore from the companion VM to install iOS.",
        "platforms": ["windows", "linux", "macos"],
        "automated": False,
        "manual_instructions": (
            "1. Start the companion VM FIRST\n"
            "2. Then start the main Inferno VM with -initrd flag\n"
            "3. In the companion VM, run:\n\n"
            "   idevicerestore --erase --restore-mode \\\n"
            "     -i 0x1122334455667788 \\\n"
            "     iPhone11,8,iPhone12,1_14.0_18A5351d_Restore.ipsw \\\n"
            "     -T root_ticket.der\n\n"
            "The VM will close after restore stage 1.\n"
            "Apply filesystem patches before completing data migration.\n\n"
            "Full guide: https://chefkiss.dev/guides/inferno/running-restoring/"
        ),
    },
    {
        "id": "fs_patches",
        "name": "Filesystem Patches",
        "description": "Patch the dyld shared cache for software rendering (macOS only).",
        "platforms": ["macos"],
        "automated": True,
        "script_fn": _script_fs_patches,
        "manual_instructions": (
            "Filesystem patches require macOS (hdiutil + diskutil).\n\n"
            "On Linux/Windows, you need a macOS VM or access to a Mac.\n"
            "Mount the root disk, then run InfernoFSPatcher on the\n"
            "dyld_shared_cache_arm64e file.\n\n"
            "Full guide: https://chefkiss.dev/guides/inferno/fs-patches/"
        ),
    },
    {
        "id": "install_bootstrap",
        "name": "Install Bootstrap",
        "description": "Install the checkra1n bootstrap (Sileo + bash) onto the root disk.",
        "platforms": ["windows", "linux", "macos"],
        "automated": False,
        "manual_instructions": (
            "Use the 'Install Sileo' button in the main window's\n"
            "Emulator panel (with the emulator stopped).\n\n"
            "Or manually:\n"
            "  1. Mount the root disk image\n"
            "  2. curl -LO $(curl https://assets.checkra.in/loader/"
            "config.json | jq -r '.core_bootstrap_tar')\n"
            "  3. sudo tar xf strap.tar.lzma -C /mount/point\n"
            "  4. Edit launchd.plist to add bash daemon\n"
            "  5. Unmount\n\n"
            "Full guide: https://chefkiss.dev/guides/inferno-post-setup/"
            "jailbreak-bootstrap/"
        ),
    },
]


def get_steps_for_platform(platform):
    """Return only the steps applicable to the given platform."""
    return [s for s in SETUP_STEPS if platform in s["platforms"]]


def get_script_for_step(step_id, platform, work_dir):
    """Generate the bash script for a step, or None if manual."""
    for step in SETUP_STEPS:
        if step["id"] == step_id:
            if not step.get("automated", False):
                return None
            fn = step.get("script_fn")
            if fn is None:
                return None
            return fn(platform, work_dir)
    return None
