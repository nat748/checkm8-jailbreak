"""
Inferno (QEMU-based iPhone 11 emulator) launch configuration.

The emulator runs in WSL (Ubuntu) from the user's home directory where
the Inferno build and iOS firmware files are already set up.
"""

import subprocess
import threading

WSL_DISTRO = "Ubuntu"

# QEMU arguments as a list — avoids shell quoting issues entirely.
# Each logical argument is one entry. Runs from WSL home directory.
QEMU_ARGS = [
    "./Inferno/build/qemu-system-aarch64",
    "-M", "t8030,trustcache=./Restore/Firmware/038-44135-124.dmg.trustcache,ticket=root_ticket.der,sep-fw=sep-firmware.n104.RELEASE.new.img4,sep-rom=AppleSEPROM-Cebu-B1,kaslr-off=true,usb-conn-type=unix,usb-conn-addr=/tmp/InfernoUSBRemote",
    "-kernel", "./Restore/kernelcache.research.iphone12b",
    "-dtb", "./Restore/Firmware/all_flash/DeviceTree.n104ap.im4p",
    "-initrd", "./Restore/038-44135-124.dmg",
    "-append", "tlto_us=-1 mtxspin=-1 agm-genuine=1 agm-authentic=1 agm-trusted=1 serial=3 launchd_unsecure_cache=1 wdt=-1 -vm_compressor_wk_sw launchd_unsecure_cache=1",
    "-smp", "7", "-m", "4G", "-serial", "mon:stdio",
    "-display", "gtk,zoom-to-fit=on,show-cursor=on",
    "-drive", "file=sep_nvram,if=pflash,format=raw",
    "-drive", "file=sep_ssc,if=pflash,format=raw",
    "-drive", "file=root,format=raw,if=none,id=root",
    "-device", "nvme-ns,drive=root,bus=nvme-bus.0,nsid=1,nstype=1,logical_block_size=4096,physical_block_size=4096",
    "-drive", "file=firmware,format=raw,if=none,id=firmware",
    "-device", "nvme-ns,drive=firmware,bus=nvme-bus.0,nsid=2,nstype=2,logical_block_size=4096,physical_block_size=4096",
    "-drive", "file=syscfg,format=raw,if=none,id=syscfg",
    "-device", "nvme-ns,drive=syscfg,bus=nvme-bus.0,nsid=3,nstype=3,logical_block_size=4096,physical_block_size=4096",
    "-drive", "file=ctrl_bits,format=raw,if=none,id=ctrl_bits",
    "-device", "nvme-ns,drive=ctrl_bits,bus=nvme-bus.0,nsid=4,nstype=4,logical_block_size=4096,physical_block_size=4096",
    "-drive", "file=nvram,if=none,format=raw,id=nvram",
    "-device", "apple-nvram,drive=nvram,bus=nvme-bus.0,nsid=5,nstype=5,id=nvram,logical_block_size=4096,physical_block_size=4096",
    "-drive", "file=effaceable,format=raw,if=none,id=effaceable",
    "-device", "nvme-ns,drive=effaceable,bus=nvme-bus.0,nsid=6,nstype=6,logical_block_size=4096,physical_block_size=4096",
    "-drive", "file=panic_log,format=raw,if=none,id=panic_log",
    "-device", "nvme-ns,drive=panic_log,bus=nvme-bus.0,nsid=7,nstype=8,logical_block_size=4096,physical_block_size=4096",
]


def _build_shell_command():
    """Build a properly quoted shell command string for bash -c."""
    import shlex
    return "cd ~ && " + " ".join(shlex.quote(a) for a in QEMU_ARGS)


class EmulatorProcess:
    """Manages the Inferno QEMU process running in WSL Ubuntu."""

    def __init__(self, log_callback=None):
        self._log_cb = log_callback or (lambda *a: None)
        self._process = None
        self._reader_thread = None
        self._status_callback = None

    @property
    def running(self):
        return self._process is not None and self._process.poll() is None

    def start(self, status_callback=None):
        """Launch Inferno in WSL Ubuntu. Returns True if started successfully."""
        if self.running:
            return False

        self._status_callback = status_callback

        shell_cmd = _build_shell_command()
        wsl_cmd = ["wsl", "-d", WSL_DISTRO, "--", "bash", "-c", shell_cmd]

        self._log_cb("info", f"WSL distro: {WSL_DISTRO}")
        self._log_cb("info", f"Running: {QEMU_ARGS[0]}")

        try:
            self._process = subprocess.Popen(
                wsl_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self._log_cb("error", "WSL not found. Is WSL installed?")
            return False
        except OSError as e:
            self._log_cb("error", f"Failed to start emulator: {e}")
            return False

        # Read stdout in a background thread
        self._reader_thread = threading.Thread(
            target=self._read_output, daemon=True,
        )
        self._reader_thread.start()
        return True

    def stop(self):
        """Terminate the emulator process."""
        if not self.running:
            return
        try:
            self._process.terminate()
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
        finally:
            self._process = None
            if self._status_callback:
                self._status_callback("stopped")

    def _read_output(self):
        """Read process stdout and forward to log callback."""
        if self._status_callback:
            self._status_callback("running")

        try:
            for line in self._process.stdout:
                line = line.rstrip("\n\r")
                if line:
                    self._log_cb("info", f"[EMU] {line}")
        except (ValueError, OSError):
            pass

        # Process ended
        exit_code = self._process.poll() if self._process else None
        self._process = None

        if exit_code and exit_code != 0:
            self._log_cb("warning", f"Emulator exited with code {exit_code}")
            if self._status_callback:
                self._status_callback("error")
        else:
            self._log_cb("info", "Emulator stopped")
            if self._status_callback:
                self._status_callback("stopped")
