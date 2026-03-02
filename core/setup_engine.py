"""
Setup engine for emulator installation.

Executes setup steps as bash scripts — via WSL on Windows,
directly on macOS/Linux.  Follows the same subprocess pattern
as BootstrapInstaller (stdin pipe, readline loop, structured
output parsing).

Supports both Inferno and pongoOS setup.
"""

import subprocess
import threading

from config.emulator_config import WSL_DISTRO
from config.setup_steps import get_script_for_step as get_inferno_script
from config.pongoos_setup import get_script_for_step as get_pongoos_script


class SetupEngine:
    """Runs individual setup steps with progress and log reporting."""

    def __init__(self, platform, work_dir, emulator_type="inferno", sudo_password=None, log_callback=None, step_callback=None):
        """
        Args:
            platform: 'windows', 'macos', 'macos-arm64', or 'linux'
            work_dir: absolute path for emulator files (WSL path on Windows)
            emulator_type: 'inferno' or 'pongoos'
            sudo_password: password for sudo operations (None = will prompt)
            log_callback: fn(level, message)
            step_callback: fn(step_id, status)  — status is
                           'running', 'done', 'failed'
        """
        self._platform = platform
        self._work_dir = work_dir
        self._emulator_type = emulator_type
        self._sudo_password = sudo_password
        self._log_cb = log_callback or (lambda *a: None)
        self._step_cb = step_callback or (lambda *a: None)
        self._cancel_event = threading.Event()
        self._process = None

    def set_sudo_password(self, password):
        """Set the sudo password for subsequent operations."""
        self._sudo_password = password

    def cancel(self):
        self._cancel_event.set()
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def run_step(self, step_id):
        """Execute a single setup step.  Call from a background thread.

        Returns True on success, False on failure.
        """
        self._cancel_event.clear()

        # Get the correct script function based on emulator type
        if self._emulator_type == "pongoos":
            script = get_pongoos_script(step_id, self._platform, self._work_dir)
        else:
            script = get_inferno_script(step_id, self._platform, self._work_dir)

        if script is None:
            self._log("warning", "This step requires manual action.")
            return False

        # Wrap script with mkdir + cd into work_dir
        # Clean work_dir first to ensure no line endings in path
        clean_work_dir = self._work_dir.replace("\r", "").replace("\n", "")
        preamble = f'mkdir -p "{clean_work_dir}" && cd "{clean_work_dir}"\n'
        full_script = preamble + script

        self._step_cb(step_id, "running")
        self._log("info", f"Running step: {step_id}")

        success = self._execute(full_script)

        self._step_cb(step_id, "done" if success else "failed")
        return success

    def _execute(self, script):
        """Run a bash script and parse its output."""
        try:
            if self._platform == "windows":
                cmd = ["wsl", "-d", WSL_DISTRO, "--", "bash"]
            else:
                cmd = ["bash", "-e"]  # Exit on error

            # Clean script - aggressively remove ALL Windows line endings
            # Must do this BEFORE adding preamble
            clean_script = script.replace("\r\n", "\n").replace("\r", "\n")

            # Remove any trailing whitespace from each line
            clean_script = "\n".join(line.rstrip() for line in clean_script.split("\n"))

            # Inject sudo password if provided
            if self._sudo_password:
                # Escape single quotes in password for bash
                escaped_pwd = self._sudo_password.replace("'", "'\\''")
                pwd_line = f"SUDO_PASSWORD='{escaped_pwd}'\n"
                clean_script = pwd_line + clean_script
                # Replace sudo -n with piped password sudo -S
                clean_script = clean_script.replace("sudo -n", "echo \"$SUDO_PASSWORD\" | sudo -S")

            # Add error handling (with Unix line endings only)
            clean_script = "set -e\nset -o pipefail\n" + clean_script

            # Final cleanup - ensure no \r anywhere
            clean_script = clean_script.replace("\r", "")

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            # DEBUG: Log first 500 chars of clean script to see what we're sending
            debug_script = clean_script.replace('\r', '')
            import sys
            with open('C:/Users/natha/script_debug.txt', 'w', encoding='utf-8', newline='\n') as f:
                f.write(debug_script[:1000])
                f.write("\n\n=== REPR ===\n")
                f.write(repr(debug_script[:500]))

            # Final replace right before writing - text mode on Windows
            # will convert \n to \r\n, so strip any \r that got added
            self._process.stdin.write(debug_script)
            self._process.stdin.close()

            while True:
                line = self._process.stdout.readline()
                if not line:
                    break

                if self._cancel_event.is_set():
                    self._process.terminate()
                    self._log("warning", "Step cancelled")
                    return False

                line = line.rstrip("\n\r")
                if not line:
                    continue

                if line.startswith("SS_INFO:"):
                    self._log("info", line[8:])
                elif line.startswith("SS_WARN:"):
                    self._log("warning", line[8:])
                elif line.startswith("SS_ERROR:"):
                    self._log("error", line[9:])
                elif line.startswith("SS_STEP:"):
                    pass  # reserved for future sub-step progress
                else:
                    self._log("info", line)

            exit_code = self._process.wait()
            self._process = None

            if exit_code == 0:
                self._log("success", "Step completed successfully")
                return True
            else:
                self._log("error", f"Step failed (exit code {exit_code})")
                return False

        except FileNotFoundError:
            msg = "WSL not found" if self._platform == "windows" else "bash not found"
            self._log("error", msg)
            return False
        except Exception as e:
            self._log("error", f"Error: {e}")
            return False

    def _log(self, level, msg):
        self._log_cb(level, msg)
