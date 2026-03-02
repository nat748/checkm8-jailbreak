"""
Main application window with Apple-style liquid glass UI.

Layout uses relative place() positioning (relx/rely/relwidth/relheight)
so panels scale automatically on resize without any event handler.
A tkinter Canvas sits behind everything with the animated fluid
background; glass panels float on top.
"""

import queue
import threading
import ctypes
import tkinter as tk
import customtkinter as ctk

from config.constants import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_BG,
    COLOR_GLASS,
    COLOR_GLASS_BORDER,
    COLOR_GLASS_LIGHT,
    COLOR_ACCENT,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
    GITHUB_OWNER,
    GITHUB_REPO,
)
from config.themes import toggle_theme, get_current_theme, save_theme_preference, load_theme_preference
from config.device_configs import get_config_for_cpid
from config.emulator_config import EmulatorProcess
from core.usb_device import DFUDevice, DeviceInfo
from core.exploit_engine import ExploitEngine
from core.emulator_exploit import EmulatorExploitEngine, _EMULATED_CONFIG
from core.bootstrap import BootstrapInstaller
from gui.fluid_background import FluidBackground
from gui.device_panel import DevicePanel
from gui.exploit_panel import ExploitPanel
from gui.emulator_panel import EmulatorPanel
from gui.log_panel import LogPanel
from gui.setup_window import SetupWindow
from gui.about_window import AboutWindow
from gui.update_dialog import show_update_dialog
from gui.pongoos_panel import PongoOSPanel
from gui.pongoos_console import PongoOSConsole
from gui.package_manager_dialog import PackageManagerDialog
from gui.password_dialog import PasswordDialog
from core.updater import check_for_updates_async
from core.pongoos_emulator import PongoOSEmulator


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(900, 750)  # Increased to fit all panels
        self.configure(fg_color=COLOR_BG)

        # State
        self._device = None
        self._device_config = None
        self._engine = None
        self._exploit_thread = None
        self._emulator = None
        self._emulator_mode = False  # True when using emulator for exploit
        self._bootstrap_installer = None
        self._bootstrap_thread = None
        self._setup_window = None
        self._about_window = None
        self._update_dialog = None
        self._pongoos = None
        self._pongoos_console = None
        self._sudo_password = None  # Cached sudo password for bootstrap
        self._log_queue = queue.Queue()
        self._progress_queue = queue.Queue()

        # Windows 11: rounded corners + optional acrylic
        self.after(50, self._apply_win11_effects)

        # ---- Background canvas (layer 0) ----
        self._canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self._fluid = FluidBackground(self._canvas)

        # ---- Glass panels (layer 1, relative positioning) ----
        # All values are fractions of the window so layout is automatic.
        M = 0.012  # margin (1.2%)
        G = 0.010  # gap between panels
        HEADER_H = 0.062
        LEFT_W = 0.285
        TOP = M + HEADER_H + G

        # Header
        self._header = ctk.CTkFrame(
            self, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
        )
        self._header.place(relx=M, rely=M, relwidth=1 - M * 2, relheight=HEADER_H)

        title = ctk.CTkLabel(
            self._header, text="checkm8",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_ACCENT,
        )
        title.pack(side="left", padx=22)

        # Theme switcher button
        current_theme = get_current_theme()
        theme_icon = "☾" if current_theme["name"] == "light" else "☀"
        self._theme_btn = ctk.CTkButton(
            self._header, text=theme_icon,
            font=ctk.CTkFont(size=16),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_DIM, height=28, width=40, corner_radius=8,
            command=self._on_theme_toggle,
        )
        self._theme_btn.pack(side="right", padx=(0, 22))

        ctk.CTkButton(
            self._header, text="About",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_DIM, height=28, width=60, corner_radius=8,
            command=self._on_about_clicked,
        ).pack(side="right", padx=(0, 8))

        ver = ctk.CTkLabel(
            self._header, text=APP_VERSION,
            font=ctk.CTkFont(family="Consolas", size=11), text_color=COLOR_TEXT_DIM,
        )
        ver.pack(side="right", padx=6)

        # Left column panel heights (adjusted to fit all panels with scrolling room)
        DEV_H = 0.20   # Device panel
        EXP_H = 0.21   # Exploit panel
        EMU_H = 0.19   # Inferno Emulator panel
        PONGO_H = 0.17 # pongoOS Emulator panel

        # Device panel
        self._device_panel = DevicePanel(self, on_detect=self._on_detect_clicked)
        self._device_panel.place(
            relx=M, rely=TOP,
            relwidth=LEFT_W, relheight=DEV_H,
        )

        # Exploit panel
        self._exploit_panel = ExploitPanel(
            self,
            on_exploit=self._on_exploit_clicked,
            on_cancel=self._on_cancel_clicked,
        )
        exp_top = TOP + DEV_H + G
        self._exploit_panel.place(
            relx=M, rely=exp_top,
            relwidth=LEFT_W, relheight=EXP_H,
        )

        # Inferno Emulator panel
        self._emulator_panel = EmulatorPanel(
            self,
            on_launch=self._on_emulator_launch,
            on_stop=self._on_emulator_stop,
            on_bootstrap=self._on_bootstrap_clicked,
            on_setup=self._on_setup_clicked,
        )
        emu_top = exp_top + EXP_H + G
        self._emulator_panel.place(
            relx=M, rely=emu_top,
            relwidth=LEFT_W, relheight=EMU_H,
        )

        # pongoOS Emulator panel
        self._pongoos_panel = PongoOSPanel(
            self,
            on_launch=self._on_pongoos_launch,
            on_stop=self._on_pongoos_stop,
            on_setup=self._on_pongoos_setup,
            on_console=self._on_pongoos_console,
        )
        pongo_top = emu_top + EMU_H + G
        self._pongoos_panel.place(
            relx=M, rely=pongo_top,
            relwidth=LEFT_W, relheight=PONGO_H,
        )

        # DFU guide card (smaller now)
        self._dfu_card = self._make_dfu_card()
        dfu_top = pongo_top + PONGO_H + G
        self._dfu_card.place(
            relx=M, rely=dfu_top,
            relwidth=LEFT_W, relheight=1 - dfu_top - M,
        )

        # Log panel (fills right side)
        self._log_panel = LogPanel(self)
        self._log_panel.place(
            relx=M + LEFT_W + G,
            rely=TOP,
            relwidth=1 - M * 2 - LEFT_W - G,
            relheight=1 - TOP - M,
        )

        # Lift all panels above the canvas
        for w in (self._header, self._device_panel, self._exploit_panel,
                  self._emulator_panel, self._pongoos_panel, self._dfu_card, self._log_panel):
            w.lift()

        # Start
        self._fluid.start()
        self._poll_queues()

        # Welcome log
        self._log_panel.log("info", f"{APP_NAME} v{APP_VERSION}")
        self._log_panel.log_separator()
        self._log_panel.log("info", "Connect device in DFU mode, then Detect.")

        # Check for updates in background (non-blocking)
        if GITHUB_OWNER != "YOUR_USERNAME":  # Only if configured
            self.after(2000, self._check_for_updates)

    # ---- Win11 effects ----

    def _apply_win11_effects(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            # Force rounded corners (DWMWA_WINDOW_CORNER_PREFERENCE = 33)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33,
                ctypes.byref(ctypes.c_int(2)),  # DWMWCP_ROUND
                ctypes.sizeof(ctypes.c_int),
            )
            # Attempt acrylic backdrop (DWMWA_SYSTEMBACKDROP_TYPE = 38)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 38,
                ctypes.byref(ctypes.c_int(3)),  # acrylic
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    # ---- DFU card ----

    def _make_dfu_card(self):
        card = ctk.CTkFrame(
            self, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
        )

        ctk.CTkLabel(
            card, text="DFU Mode",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_TEXT_DIM,
        ).pack(padx=18, pady=(14, 6), anchor="w")

        for step in [
            "1  Power off the device",
            "2  Hold Power + Home for 10 sec",
            "3  Release Power, keep holding Home",
            "4  Screen stays black = DFU mode",
        ]:
            ctk.CTkLabel(
                card, text=step,
                font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM, anchor="w",
            ).pack(padx=22, anchor="w", pady=1)

        ctk.CTkLabel(
            card,
            text="iPhone 7+: use Volume Down\ninstead of Home button",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_DIM,
            anchor="w", justify="left",
        ).pack(padx=22, pady=(6, 14), anchor="w")

        return card

    # ---- Queue polling ----

    def _poll_queues(self):
        try:
            while True:
                level, msg = self._log_queue.get_nowait()
                self._log_panel.log(level, msg)
        except queue.Empty:
            pass
        try:
            while True:
                stage, pct = self._progress_queue.get_nowait()
                self._exploit_panel.update_progress(stage, pct)
        except queue.Empty:
            pass
        self.after(16, self._poll_queues)

    def _log_t(self, level, msg):
        self._log_queue.put((level, msg))

    def _progress_t(self, stage, pct):
        self._progress_queue.put((stage, pct))

    # ---- Detection ----

    def _on_detect_clicked(self):
        self._device_panel.set_detecting()
        self._exploit_panel.reset()
        self._emulator_mode = False

        # If emulator is running, detect it directly
        if self._emulator and self._emulator.running:
            self._log_panel.log("info", "Detecting emulated device...")
            threading.Thread(target=self._detect_emulator_worker, daemon=True).start()
        else:
            self._log_panel.log("info", "Scanning for DFU device...")
            threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_emulator_worker(self):
        """Detect the emulated iPhone 11 from the running Inferno instance."""
        import time, random
        time.sleep(0.5)  # Brief scan delay

        if not self._emulator or not self._emulator.running:
            self._log_t("warning", "Emulator stopped during detection")
            self.after(0, self._device_panel.set_not_found)
            return

        # Build emulated device info
        info = DeviceInfo()
        info.cpid = 0x8030
        info.cprv = 0x11
        info.bdid = 0x04
        info.ecid = random.randint(0x0001000000000000, 0x00FFFFFFFFFFFFFF)
        info.srtg = "iBoot-4479.0.0.100.4"
        info.serial_string = (
            f"CPID:8030 CPRV:11 CPFM:03 SCEP:01 BDID:04 "
            f"ECID:{info.ecid:016X} IBFL:3C "
            f"SRTG:[iBoot-4479.0.0.100.4]"
        )

        config = _EMULATED_CONFIG
        self._device_config = config
        self._emulator_mode = True

        self._log_t("success", "Emulated device found!")
        self._log_t("info", f"CPID: 0x{info.cpid:04X} (emulated)")
        self._log_t("info", f"Chip: {config['name']}")
        self._log_t("info", f"Target: {', '.join(config['devices'])}")
        self._log_t("info", "Mode: Inferno emulator (kernel-patched jailbreak)")

        self.after(0, lambda: self._device_panel.set_device_info(info, config))
        self.after(0, self._exploit_panel.enable_exploit)

    def _detect_worker(self):
        try:
            device = DFUDevice.find(timeout=8.0)
            if device is None:
                self._log_t("warning", "No device found in DFU mode")
                self.after(0, self._device_panel.set_not_found)
                return

            cpid = device.info.cpid
            config = get_config_for_cpid(cpid)
            self._device = device
            self._device_config = config

            self._log_t("success", "Device found!")
            self._log_t("info", f"CPID: 0x{cpid:04X}")
            if config:
                self._log_t("info", f"Chip: {config['name']}")

            self.after(0, lambda: self._device_panel.set_device_info(device.info, config))
            if config:
                self.after(0, self._exploit_panel.enable_exploit)
            else:
                self.after(0, self._exploit_panel.disable_exploit)
                self._log_t("error", "Unsupported chip")
        except Exception as e:
            self._log_t("error", f"Detection error: {e}")
            self.after(0, lambda: self._device_panel.set_error(str(e)))

    # ---- Exploit ----

    def _on_exploit_clicked(self):
        if self._exploit_thread and self._exploit_thread.is_alive():
            return
        self._exploit_panel.set_running()
        self._log_panel.log_separator()

        if self._emulator_mode and self._emulator and self._emulator.running:
            # Use emulator exploit engine
            self._engine = EmulatorExploitEngine(
                self._emulator,
                progress_callback=self._progress_t,
                log_callback=self._log_t,
            )
        else:
            # Use real USB exploit engine
            if self._device:
                self._device.release()
                self._device = None

            self._engine = ExploitEngine(
                progress_callback=self._progress_t,
                log_callback=self._log_t,
            )

        self._exploit_thread = threading.Thread(
            target=self._exploit_worker, daemon=True,
        )
        self._exploit_thread.start()

    def _exploit_worker(self):
        result = self._engine.run()
        self.after(0, lambda: self._exploit_panel.set_finished(result.success))
        self._log_t("success" if result.success else "error", result.message)

    def _on_cancel_clicked(self):
        if self._engine:
            self._engine.cancel()
            self._log_t("warning", "Cancelling...")

    # ---- Emulator ----

    def _on_emulator_launch(self):
        if self._emulator and self._emulator.running:
            return
        self._emulator_panel.set_launching()
        self._log_panel.log_separator()
        self._log_panel.log("info", "Launching Inferno emulator via WSL...")

        # Pause background animation to free CPU for QEMU
        self._fluid.stop()

        self._emulator = EmulatorProcess(log_callback=self._log_t)
        started = self._emulator.start(
            status_callback=self._emulator_status_changed,
        )
        if not started:
            self._fluid.start()
            self.after(0, lambda: self._emulator_panel.set_error("Failed to start"))

    def _emulator_status_changed(self, status):
        """Called from the emulator reader thread."""
        if status == "running":
            self.after(0, self._emulator_panel.set_running)
            self._log_t("success", "Emulator is running")
        elif status == "stopped":
            self.after(0, self._emulator_panel.set_stopped)
            self.after(0, self._fluid.start)
        elif status == "error":
            self.after(0, lambda: self._emulator_panel.set_error("Crashed"))
            self.after(0, self._fluid.start)

    def _on_emulator_stop(self):
        if self._emulator and self._emulator.running:
            self._log_panel.log("info", "Stopping emulator...")
            self._emulator.stop()
            self._emulator_panel.set_stopped()
            self._fluid.start()
            self._log_panel.log("info", "Emulator stopped")

    # ---- Bootstrap (Sileo) ----

    def _on_bootstrap_clicked(self):
        if self._bootstrap_thread and self._bootstrap_thread.is_alive():
            return
        if self._emulator and self._emulator.running:
            self._log_panel.log(
                "warning",
                "Stop the emulator first — the root disk can't be "
                "modified while QEMU is running.",
            )
            return

        # Show package manager selection dialog
        dialog = PackageManagerDialog(self)
        pkg_choice = dialog.get_selection()

        if pkg_choice is None:
            # User cancelled
            return

        # Prompt for sudo password if not already set
        if not self._sudo_password:
            pwd_dialog = PasswordDialog(self)
            password = pwd_dialog.get_password()
            if not password:
                # User cancelled
                return
            self._sudo_password = password

        self._emulator_panel.set_bootstrap_running(pkg_choice)
        self._log_panel.log_separator()
        self._log_panel.log("info", f"Installing {pkg_choice.capitalize()} package manager...")

        self._bootstrap_installer = BootstrapInstaller(
            package_manager=pkg_choice,
            sudo_password=self._sudo_password,
            log_callback=self._log_t,
            progress_callback=self._progress_t,
        )
        self._bootstrap_thread = threading.Thread(
            target=self._bootstrap_worker, daemon=True,
        )
        self._bootstrap_thread.start()

    def _bootstrap_worker(self):
        success = self._bootstrap_installer.install()
        self.after(0, lambda: self._emulator_panel.set_bootstrap_done(success))

    # ---- Setup wizard ----

    def _on_setup_clicked(self):
        if self._setup_window and self._setup_window.winfo_exists():
            self._setup_window.focus()
            return
        self._setup_window = SetupWindow(self, emulator_type="inferno")

    # ---- Theme Switcher ----

    def _on_theme_toggle(self):
        """Toggle between light and dark themes."""
        new_theme = toggle_theme()
        save_theme_preference()

        # Show message
        theme_name = "Light Mode" if new_theme["name"] == "light" else "Dark Mode"
        self._log_panel.log("info", f"Switched to {theme_name}.")
        self._log_panel.log("info", "Restarting app to apply theme...")

        # Restart the app to apply theme
        self.after(1000, self._restart_app)

    def _restart_app(self):
        """Restart the application."""
        import sys
        import os
        self.destroy()
        # Relaunch the app
        os.execl(sys.executable, sys.executable, *sys.argv)

    # ---- About ----

    def _on_about_clicked(self):
        if self._about_window and self._about_window.winfo_exists():
            self._about_window.focus()
            return
        self._about_window = AboutWindow(self, on_check_updates=self._check_for_updates)

    # ---- Updates ----

    def _check_for_updates(self):
        """Check for updates from GitHub releases."""
        if GITHUB_OWNER == "YOUR_USERNAME":
            self._log_panel.log("warning", "Update check skipped - GitHub repo not configured")
            return

        def on_update_result(update_available: bool, release_info: dict):
            if update_available and release_info:
                # Show update dialog on UI thread
                self.after(0, lambda: self._show_update_dialog(release_info))

        check_for_updates_async(GITHUB_OWNER, GITHUB_REPO, on_update_result)

    def _show_update_dialog(self, release_info: dict):
        """Show update notification dialog."""
        if self._update_dialog and self._update_dialog.winfo_exists():
            self._update_dialog.focus()
            return

        self._update_dialog = show_update_dialog(self, release_info)
        self._log_panel.log("info", f"Update available: v{release_info['version']}")

    # ---- pongoOS Emulator ----

    def _on_pongoos_launch(self):
        """Launch pongoOS emulator."""
        if self._pongoos and self._pongoos.running:
            return

        self._pongoos_panel.set_launching()
        self._log_panel.log_separator()
        self._log_panel.log("info", "Launching pongoOS emulator...")

        # Create emulator instance
        self._pongoos = PongoOSEmulator(log_callback=self._log_t)

        # Start in background thread to avoid blocking
        def start_worker():
            started = self._pongoos.start(
                status_callback=self._pongoos_status_changed
            )
            if not started:
                self.after(0, lambda: self._pongoos_panel.set_error("Failed to start"))

        threading.Thread(target=start_worker, daemon=True).start()

    def _pongoos_status_changed(self, status):
        """Called from pongoOS monitor thread."""
        if status == "running":
            self.after(0, self._pongoos_panel.set_running)
            self._log_t("success", "pongoOS emulator is running")
        elif status == "stopped":
            self.after(0, self._pongoos_panel.set_stopped)
        elif status == "error":
            self.after(0, lambda: self._pongoos_panel.set_error("Crashed"))

    def _on_pongoos_stop(self):
        """Stop pongoOS emulator."""
        if self._pongoos and self._pongoos.running:
            self._log_panel.log("info", "Stopping pongoOS emulator...")
            self._pongoos.stop()
            self._pongoos_panel.set_stopped()
            self._log_panel.log("info", "pongoOS emulator stopped")

    def _on_pongoos_setup(self):
        """Open setup wizard for pongoOS."""
        if self._setup_window and self._setup_window.winfo_exists():
            self._setup_window.focus()
            return
        self._setup_window = SetupWindow(self, emulator_type="pongoos")

    def _on_pongoos_console(self):
        """Open pongoOS console window."""
        if self._pongoos_console and self._pongoos_console.winfo_exists():
            self._pongoos_console.focus()
            return

        def send_command(cmd):
            if self._pongoos and self._pongoos.running:
                self._pongoos.send_command(cmd)

        self._pongoos_console = PongoOSConsole(self, on_send_command=send_command)

        # Redirect pongoOS output to console
        old_log = self._pongoos._log if self._pongoos else None

        def new_log(level, msg):
            if old_log:
                old_log(level, msg)
            if self._pongoos_console and self._pongoos_console.winfo_exists():
                self._pongoos_console.append_output(f"{msg}\n")
