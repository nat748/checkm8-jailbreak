"""
Setup engine for Inferno emulator installation.

Executes setup steps as bash scripts — via WSL on Windows,
directly on macOS/Linux.  Follows the same subprocess pattern
as BootstrapInstaller (stdin pipe, readline loop, structured
output parsing).
"""

import subprocess
import threading

from config.emulator_config import WSL_DISTRO
from config.setup_steps import get_script_for_step


class SetupEngine:
    """Runs individual setup steps with progress and log reporting."""

    def __init__(self, platform, work_dir, log_callback=None, step_callback=None):
        """
        Args:
            platform: 'windows', 'macos', or 'linux'
            work_dir: absolute path for Inferno files (WSL path on Windows)
            log_callback: fn(level, message)
            step_callback: fn(step_id, status)  — status is
                           'running', 'done', 'failed'
        """
        self._platform = platform
        self._work_dir = work_dir
        self._log_cb = log_callback or (lambda *a: None)
        self._step_cb = step_callback or (lambda *a: None)
        self._cancel_event = threading.Event()
        self._process = None

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

        script = get_script_for_step(step_id, self._platform, self._work_dir)
        if script is None:
            self._log("warning", "This step requires manual action.")
            return False

        # Wrap script with mkdir + cd into work_dir
        preamble = f'mkdir -p "{self._work_dir}" && cd "{self._work_dir}"\n'
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
                cmd = ["bash"]

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._process.stdin.write(script.replace("\r", ""))
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
