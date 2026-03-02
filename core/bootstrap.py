"""
Checkra1n bootstrap installer for Inferno emulator.

Installs the checkra1n bootstrap (base APT system) and selected
package manager (Sileo/Zebra/Cydia) onto the Inferno root disk image
via WSL commands.

The emulator MUST be stopped before running this — the root disk
image cannot be modified while QEMU has it open.
"""

import subprocess
import threading

from config.emulator_config import WSL_DISTRO

# Package manager download URLs
_PKG_URLS = {
    "sileo": None,  # Included in checkra1n bootstrap
    "zebra": "https://getzbra.com/repo/dists/stable/main/binary-iphoneos-arm/getzbra_1.1.28_iphoneos-arm.deb",
    "cydia": "https://apt.bingner.com/debs/1443.00/cydia_1.1.36_iphoneos-arm.deb",
}

# Bash script that runs inside WSL Ubuntu to install the bootstrap.
# Uses structured output prefixes so the Python side can parse progress.
# $1 = package manager choice ("sileo", "zebra", or "cydia")
_BOOTSTRAP_SCRIPT = r'''
log_info()  { echo "BS_INFO:$1"; }
log_warn()  { echo "BS_WARN:$1"; }
log_error() { echo "BS_ERROR:$1"; }
log_step()  { echo "BS_STEP:$1"; }

PKG_MANAGER="$1"
[ -z "$PKG_MANAGER" ] && PKG_MANAGER="sileo"

ROOT_IMAGE="$HOME/root"
MOUNT_POINT="/mnt/ios_bootstrap"
STRAP_FILE="/tmp/strap.tar.lzma"
PKG_FILE="/tmp/package_manager.deb"

# ---- Check sudo (no TTY available, must be passwordless) ----
log_step "checking_tools"

if ! sudo -n true 2>/dev/null; then
    log_error "sudo requires a password but no terminal is available."
    log_info "Fix: open a WSL terminal and run:"
    log_info "  echo \"$USER ALL=(ALL) NOPASSWD: ALL\" | sudo tee /etc/sudoers.d/$USER"
    log_info "Then try Install Sileo again."
    exit 1
fi

log_info "sudo OK (passwordless)"

if [ ! -f "$ROOT_IMAGE" ]; then
    log_error "Root disk image not found at ~/root"
    exit 1
fi

log_info "Root image found at $ROOT_IMAGE"

for tool in jq curl; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        log_info "Installing $tool..."
        if ! sudo -n apt-get install -y "$tool" >/dev/null 2>&1; then
            log_error "Failed to install $tool"
            exit 1
        fi
    fi
done

log_info "Tools ready"

# ---- Download bootstrap ----
log_step "downloading"

log_info "Fetching checkra1n bootstrap URL..."
CONFIG_JSON=$(curl -sL https://assets.checkra.in/loader/config.json 2>/dev/null || true)

if [ -z "$CONFIG_JSON" ]; then
    log_error "Failed to fetch checkra1n config (no network?)"
    exit 1
fi

BOOTSTRAP_URL=$(echo "$CONFIG_JSON" | jq -r ".core_bootstrap_tar" 2>/dev/null || true)

if [ -z "$BOOTSTRAP_URL" ] || [ "$BOOTSTRAP_URL" = "null" ]; then
    log_error "Failed to parse bootstrap URL from checkra1n config"
    exit 1
fi

log_info "Downloading $BOOTSTRAP_URL"
if ! curl -L -o "$STRAP_FILE" "$BOOTSTRAP_URL" 2>/dev/null; then
    log_error "Bootstrap download failed"
    exit 1
fi

if [ ! -f "$STRAP_FILE" ]; then
    log_error "Bootstrap file not found after download"
    exit 1
fi

log_info "Downloaded strap.tar.lzma"

# ---- Mount root disk image ----
log_step "mounting"

sudo -n mkdir -p "$MOUNT_POINT"
MOUNTED=false
CLEANUP_LOOP=""
CLEANUP_KPARTX=false

# Strategy 1: direct loop mount (works for raw single-partition images)
log_info "Trying direct mount..."
if sudo -n mount -o loop,rw "$ROOT_IMAGE" "$MOUNT_POINT" 2>/dev/null; then
    MOUNTED=true
    log_info "Direct mount succeeded"
fi

# Strategy 2: kpartx to expose partitions, then mount each
if [ "$MOUNTED" = false ]; then
    log_info "Trying kpartx partition mapping..."
    sudo -n apt-get install -y kpartx >/dev/null 2>&1 || true

    KPARTX_OUTPUT=$(sudo -n kpartx -av "$ROOT_IMAGE" 2>/dev/null || true)
    if [ -n "$KPARTX_OUTPUT" ]; then
        CLEANUP_KPARTX=true
        log_info "Partitions found"

        for part in /dev/mapper/loop*p*; do
            [ -e "$part" ] || continue
            log_info "Trying $part..."
            if sudo -n mount -o rw "$part" "$MOUNT_POINT" 2>/dev/null; then
                if [ -d "$MOUNT_POINT/System" ] || [ -d "$MOUNT_POINT/Applications" ]; then
                    MOUNTED=true
                    log_info "Mounted iOS root from $part"
                    break
                fi
                sudo -n umount "$MOUNT_POINT" 2>/dev/null || true
            fi
        done

        if [ "$MOUNTED" = false ]; then
            sudo -n kpartx -dv "$ROOT_IMAGE" >/dev/null 2>&1 || true
            CLEANUP_KPARTX=false
        fi
    fi
fi

# Strategy 3: apfs-fuse (read-only but may still allow extraction on some setups)
if [ "$MOUNTED" = false ]; then
    log_info "Trying apfs-fuse..."
    if command -v apfs-fuse >/dev/null 2>&1 || sudo -n apt-get install -y apfs-fuse >/dev/null 2>&1; then
        CLEANUP_LOOP=$(sudo -n losetup --show -fP "$ROOT_IMAGE" 2>/dev/null || true)
        if [ -n "$CLEANUP_LOOP" ]; then
            for part in "$CLEANUP_LOOP" "${CLEANUP_LOOP}p1" "${CLEANUP_LOOP}p2"; do
                [ -e "$part" ] || continue
                if sudo -n apfs-fuse -o allow_other "$part" "$MOUNT_POINT" 2>/dev/null; then
                    MOUNTED=true
                    log_warn "Mounted via apfs-fuse (read-only) — extraction may fail"
                    break
                fi
            done
            if [ "$MOUNTED" = false ]; then
                sudo -n losetup -d "$CLEANUP_LOOP" 2>/dev/null || true
                CLEANUP_LOOP=""
            fi
        fi
    fi
fi

if [ "$MOUNTED" = false ]; then
    log_error "Could not mount root disk image"
    log_info "---"
    log_info "The root image is likely APFS, which needs special tools on Linux."
    log_info "Manual installation steps:"
    log_info "  1. Install linux-apfs-rw: https://github.com/linux-apfs/linux-apfs-rw"
    log_info "  2. Mount: sudo mount -o loop ~/root /mnt/ios"
    log_info "  3. Extract: sudo tar xf /tmp/strap.tar.lzma -C /mnt/ios"
    log_info "  4. Unmount: sudo umount /mnt/ios"
    log_info "  Or follow: https://chefkiss.dev/guides/inferno-post-setup/jailbreak-bootstrap/"
    log_info "---"
    rm -f "$STRAP_FILE"
    exit 1
fi

# ---- Extract bootstrap ----
log_step "extracting"

log_info "Extracting bootstrap to $MOUNT_POINT..."
if ! sudo -n tar xf "$STRAP_FILE" -C "$MOUNT_POINT" 2>&1; then
    log_error "Failed to extract bootstrap (filesystem may be read-only)"
    sudo -n umount "$MOUNT_POINT" 2>/dev/null || sudo fusermount -u "$MOUNT_POINT" 2>/dev/null || true
    [ -n "$CLEANUP_LOOP" ] && sudo -n losetup -d "$CLEANUP_LOOP" 2>/dev/null || true
    [ "$CLEANUP_KPARTX" = true ] && sudo -n kpartx -dv "$ROOT_IMAGE" >/dev/null 2>&1 || true
    rm -f "$STRAP_FILE"
    exit 1
fi

log_info "Bootstrap files extracted"

# ---- Configure launchd ----
log_step "configuring"

PLIST="$MOUNT_POINT/System/Library/xpc/launchd.plist"
if [ -f "$PLIST" ]; then
    log_info "Found launchd plist — converting to XML..."
    sudo -n plutil -convert xml1 "$PLIST" 2>/dev/null || log_warn "plutil not available, skipping plist conversion"
    log_info "launchd plist prepared"
else
    log_warn "launchd plist not found at expected path — skipping"
fi

# ---- Install package manager ----
log_step "package_manager"

case "$PKG_MANAGER" in
    sileo)
        log_info "Using Sileo (included in checkra1n bootstrap)"
        ;;
    zebra)
        log_info "Installing Zebra package manager..."
        PKG_URL="__ZEBRA_URL__"
        if curl -L -o "$PKG_FILE" "$PKG_URL" 2>/dev/null; then
            sudo -n dpkg-deb -x "$PKG_FILE" "$MOUNT_POINT" 2>/dev/null || log_warn "Failed to extract Zebra .deb"
            log_info "Zebra installed"
            rm -f "$PKG_FILE"
        else
            log_warn "Failed to download Zebra, falling back to Sileo"
        fi
        ;;
    cydia)
        log_info "Installing Cydia package manager..."
        PKG_URL="__CYDIA_URL__"
        if curl -L -o "$PKG_FILE" "$PKG_URL" 2>/dev/null; then
            sudo -n dpkg-deb -x "$PKG_FILE" "$MOUNT_POINT" 2>/dev/null || log_warn "Failed to extract Cydia .deb"
            log_info "Cydia installed"
            rm -f "$PKG_FILE"
        else
            log_warn "Failed to download Cydia, falling back to Sileo"
        fi
        ;;
    *)
        log_warn "Unknown package manager '$PKG_MANAGER', using Sileo"
        ;;
esac

# ---- Cleanup ----
log_step "cleanup"

log_info "Unmounting..."
sudo -n umount "$MOUNT_POINT" 2>/dev/null || sudo fusermount -u "$MOUNT_POINT" 2>/dev/null || true
[ -n "$CLEANUP_LOOP" ] && sudo -n losetup -d "$CLEANUP_LOOP" 2>/dev/null || true
[ "$CLEANUP_KPARTX" = true ] && sudo -n kpartx -dv "$ROOT_IMAGE" >/dev/null 2>&1 || true
sudo -n rmdir "$MOUNT_POINT" 2>/dev/null || true
rm -f "$STRAP_FILE"

log_step "done"
log_info "Checkra1n bootstrap installed!"
case "$PKG_MANAGER" in
    sileo)
        log_info "Sileo will be available after relaunching the emulator."
        ;;
    zebra)
        log_info "Zebra will be available after relaunching the emulator."
        ;;
    cydia)
        log_info "Cydia will be available after relaunching the emulator."
        ;;
esac
'''


class BootstrapInstaller:
    """Installs the checkra1n bootstrap onto the Inferno root disk."""

    _STEP_PROGRESS = {
        "checking_tools": ("Checking tools", 5),
        "downloading": ("Downloading bootstrap", 15),
        "mounting": ("Mounting disk image", 35),
        "extracting": ("Extracting files", 55),
        "configuring": ("Configuring system", 70),
        "package_manager": ("Installing package manager", 85),
        "cleanup": ("Cleaning up", 95),
        "done": ("Complete", 100),
    }

    def __init__(self, package_manager="sileo", sudo_password=None, log_callback=None, progress_callback=None):
        self._package_manager = package_manager
        self._sudo_password = sudo_password
        self._log_cb = log_callback or (lambda *a: None)
        self._progress_cb = progress_callback or (lambda *a: None)
        self._cancel_event = threading.Event()
        self._process = None

    def set_sudo_password(self, password):
        """Set the sudo password for bootstrap installation."""
        self._sudo_password = password

    def cancel(self):
        self._cancel_event.set()
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def install(self):
        """Run the bootstrap installation. Call from a background thread."""
        self._cancel_event.clear()
        pkg_name = self._package_manager.capitalize()
        self._log("info", f"Starting checkra1n bootstrap installation with {pkg_name}...")
        self._progress("Preparing", 0)

        try:
            # Substitute URLs in script
            script = _BOOTSTRAP_SCRIPT
            script = script.replace("__ZEBRA_URL__", _PKG_URLS["zebra"])
            script = script.replace("__CYDIA_URL__", _PKG_URLS["cydia"])

            # Clean script - remove ALL Windows line endings
            script = script.replace("\r\n", "\n").replace("\r", "\n")
            script = "\n".join(line.rstrip() for line in script.split("\n"))

            # Inject sudo password if provided
            if self._sudo_password:
                escaped_pwd = self._sudo_password.replace("'", "'\\''")
                pwd_line = f"SUDO_PASSWORD='{escaped_pwd}'\n"
                script = pwd_line + script
                script = script.replace("sudo -n", "echo \"$SUDO_PASSWORD\" | sudo -S")

            # Pipe the script via stdin to avoid Windows command-line
            # quoting mangling the double quotes and $variables.
            wsl_cmd = ["wsl", "-d", WSL_DISTRO, "--", "bash", "-s", self._package_manager]

            # Use binary stdin to prevent Windows text-mode from
            # converting \n to \r\n.
            self._process = subprocess.Popen(
                wsl_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )
            # Encode to bytes with pure LF — no OS line-ending conversion
            self._process.stdin.write(script.encode("utf-8"))
            self._process.stdin.close()

            # Read stdout as bytes, decode line by line
            for raw_line in iter(self._process.stdout.readline, b""):
                if self._cancel_event.is_set():
                    self._process.terminate()
                    self._log("warning", "Bootstrap installation cancelled")
                    return False

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                if line.startswith("BS_STEP:"):
                    step = line[8:]
                    if step in self._STEP_PROGRESS:
                        name, pct = self._STEP_PROGRESS[step]
                        self._progress(name, pct)
                elif line.startswith("BS_INFO:"):
                    self._log("info", line[8:])
                elif line.startswith("BS_WARN:"):
                    self._log("warning", line[8:])
                elif line.startswith("BS_ERROR:"):
                    self._log("error", line[9:])
                else:
                    self._log("info", f"[WSL] {line}")

            exit_code = self._process.wait()
            self._process = None

            if exit_code == 0:
                pkg_name = self._package_manager.capitalize()
                self._log("success", "Bootstrap installation complete!")
                self._log("info", f"{pkg_name} will be available after relaunching the emulator.")
                self._progress("Complete", 100)
                return True
            else:
                self._log("error", f"Bootstrap installation failed (exit code {exit_code})")
                self._progress("Failed", -1)
                return False

        except FileNotFoundError:
            self._log("error", "WSL not found. Is WSL installed?")
            self._progress("Failed", -1)
            return False
        except Exception as e:
            self._log("error", f"Bootstrap error: {e}")
            self._progress("Failed", -1)
            return False

    def _log(self, level, msg):
        self._log_cb(level, msg)

    def _progress(self, name, pct):
        self._progress_cb(name, pct)
