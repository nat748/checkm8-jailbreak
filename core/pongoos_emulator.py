"""
pongoOS QEMU emulator for checkm8 testing.

Provides a virtual ARM device running pongoOS that can be exploited
via checkm8 without needing physical hardware.
"""

import subprocess
import threading
import time
import os
import platform
from pathlib import Path
from typing import Optional, Callable


class PongoOSEmulator:
    """QEMU-based pongoOS emulator."""

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize pongoOS emulator.

        Args:
            log_callback: Called with (level, message) for logging
        """
        self._log = log_callback or (lambda lvl, msg: None)
        self._process = None
        self._running = False
        self._monitor_thread = None
        self._system = platform.system().lower()

        # Use WSL path on Windows (setup wizard builds pongoOS in WSL)
        if self._system == "windows":
            # Get WSL home directory
            try:
                result = subprocess.run(
                    ["wsl", "-d", "Ubuntu", "--", "bash", "-c", "echo $HOME"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                wsl_home = result.stdout.strip()
                self._work_dir = Path(f"\\\\wsl$\\Ubuntu{wsl_home}\\PongoOSData")
                self._wsl_work_dir = f"{wsl_home}/PongoOSData"
            except Exception:
                # Fallback to default
                self._work_dir = Path.home() / "PongoOSData"
                self._wsl_work_dir = "/home/$USER/PongoOSData"
        else:
            self._work_dir = Path.home() / "PongoOSData"
            self._wsl_work_dir = str(self._work_dir)

    @property
    def running(self) -> bool:
        """Check if emulator is running."""
        return self._running and self._process and self._process.poll() is None

    def start(self, status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Start the pongoOS emulator.

        Args:
            status_callback: Called with status updates ("running", "stopped", "error")

        Returns:
            True if started successfully
        """
        if self.running:
            self._log("warning", "Emulator already running")
            return False

        # Check if pongoOS binary exists
        pongo_bin = self._work_dir / "pongoOS"
        if not pongo_bin.exists():
            self._log("error", f"pongoOS binary not found at {pongo_bin}")
            self._log("info", "Run Setup Wizard to download and build pongoOS")
            return False

        # Build QEMU command
        qemu_cmd = self._build_qemu_command(pongo_bin)
        if not qemu_cmd:
            return False

        try:
            self._log("info", "Starting QEMU with pongoOS...")

            # Start QEMU process
            if self._system == "windows":
                # Run via WSL
                self._process = subprocess.Popen(
                    ["wsl", "-d", "Ubuntu", "--"] + qemu_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    bufsize=0,
                )
            else:
                # Run directly on macOS/Linux
                self._process = subprocess.Popen(
                    qemu_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    bufsize=0,
                )

            self._running = True

            # Start monitor thread
            self._monitor_thread = threading.Thread(
                target=self._monitor_output,
                args=(status_callback,),
                daemon=True,
            )
            self._monitor_thread.start()

            self._log("success", "pongoOS emulator started")
            if status_callback:
                status_callback("running")

            return True

        except FileNotFoundError:
            self._log("error", "QEMU not found - install qemu-system-arm")
            return False
        except Exception as e:
            self._log("error", f"Failed to start emulator: {e}")
            return False

    def stop(self):
        """Stop the emulator."""
        if not self.running:
            return

        self._log("info", "Stopping pongoOS emulator...")
        self._running = False

        if self._process:
            # Send quit command to QEMU monitor
            try:
                self._process.stdin.write(b"\x01x")  # Ctrl+A X (QEMU quit)
                self._process.stdin.flush()
            except (OSError, BrokenPipeError):
                pass

            # Wait for graceful shutdown
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill
                self._process.kill()
                self._process.wait()

            self._process = None

        self._log("info", "pongoOS emulator stopped")

    def send_command(self, command: str):
        """
        Send command to pongoOS console.

        Args:
            command: Command to send (e.g., "help", "version")
        """
        if not self.running:
            return

        try:
            self._process.stdin.write(f"{command}\n".encode())
            self._process.stdin.flush()
        except Exception as e:
            self._log("error", f"Failed to send command: {e}")

    def _build_qemu_command(self, pongo_bin: Path) -> Optional[list]:
        """
        Build QEMU command line.

        Args:
            pongo_bin: Path to pongoOS binary

        Returns:
            QEMU command as list of arguments, or None if failed
        """
        # Use patched UTMapp QEMU (required for pongoOS memory layout)
        qemu_exec = "/opt/utm-qemu/bin/qemu-system-aarch64"

        # Use WSL path for kernel if on Windows
        if self._system == "windows":
            kernel_path = f"{self._wsl_work_dir}/pongoOS"
        else:
            kernel_path = str(pongo_bin)

        # Build command (using loader method from citruz/pongoOS-QEMU)
        cmd = [
            qemu_exec,
            "-M", "virt",  # Virtual ARM board
            "-cpu", "cortex-a72",  # ARM Cortex-A72 (per citruz README)
            "-accel", "tcg",  # TCG emulation
            "-m", "4096",  # 4GB RAM (per citruz README)
            "-device", f"loader,file={kernel_path},addr=0x1000,force-raw=on",  # Load pongoOS at 0x1000
            "-device", "loader,addr=0x1000,cpu-num=0",  # Set CPU entry point
            "-nographic",  # Console output only (GUI in log panel)
            "-serial", "mon:stdio",  # Serial + monitor to stdout
            "-no-reboot",  # Exit on reboot
        ]

        # Add USB controller for DFU emulation
        cmd.extend([
            "-usb",
            "-device", "usb-serial,chardev=usb0",
            "-chardev", "socket,id=usb0,host=127.0.0.1,port=1337,server=on,wait=off",
        ])

        return cmd

    def _monitor_output(self, status_callback: Optional[Callable[[str], None]]):
        """
        Monitor QEMU output in background thread.

        Args:
            status_callback: Called with status updates
        """
        if not self._process:
            return

        try:
            # Read stdout
            for line in iter(self._process.stdout.readline, b''):
                if not self._running:
                    break

                try:
                    text = line.decode('utf-8', errors='replace').strip()
                    if text:
                        self._log("info", f"[pongoOS] {text}")
                except (UnicodeDecodeError, AttributeError, OSError):
                    pass

        except Exception as e:
            self._log("error", f"Monitor error: {e}")
            if status_callback:
                status_callback("error")

        # Process ended
        self._running = False
        if status_callback:
            status_callback("stopped")


def download_pongoos(work_dir: Path, log_callback: Callable[[str, str], None]) -> bool:
    """
    Download and prepare pongoOS binary.

    Args:
        work_dir: Working directory for pongoOS files
        log_callback: Logging callback

    Returns:
        True if successful
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    log_callback("info", "Downloading pongoOS-QEMU...")

    # pongoOS-QEMU repository (optimized fork for QEMU emulation)
    repo_url = "https://github.com/karamzaki/pongoOS-QEMU.git"
    repo_dir = work_dir / "pongoOS-src"

    try:
        # Clone repo if not exists
        if not repo_dir.exists():
            log_callback("info", "Cloning pongoOS repository...")
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
                check=True,
                capture_output=True,
            )

        # Build pongoOS
        log_callback("info", "Building pongoOS...")

        # Determine build command based on platform
        system = platform.system().lower()

        if system == "windows":
            # Build via WSL
            build_cmd = [
                "wsl", "-d", "Ubuntu", "--",
                "bash", "-c",
                f"cd {repo_dir} && make"
            ]
        else:
            # Build directly
            build_cmd = ["make", "-C", str(repo_dir)]

        result = subprocess.run(
            build_cmd,
            capture_output=True,
        )

        if result.returncode != 0:
            log_callback("error", f"Build failed: {result.stderr.decode('utf-8', errors='replace')}")
            return False

        # Copy built binary
        built_bin = repo_dir / "build" / "pongoOS"
        if not built_bin.exists():
            log_callback("error", "pongoOS binary not found after build")
            return False

        target_bin = work_dir / "pongoOS"
        import shutil
        shutil.copy(built_bin, target_bin)

        log_callback("success", f"pongoOS ready at {target_bin}")
        return True

    except subprocess.CalledProcessError as e:
        log_callback("error", f"Command failed: {e}")
        return False
    except Exception as e:
        log_callback("error", f"Download failed: {e}")
        return False
