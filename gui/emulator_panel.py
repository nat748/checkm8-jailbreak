"""
Liquid glass emulator control panel.
"""

import customtkinter as ctk

from config.constants import (
    COLOR_GLASS,
    COLOR_GLASS_LIGHT,
    COLOR_GLASS_BORDER,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
)


class EmulatorPanel(ctk.CTkFrame):

    def __init__(self, parent, on_launch=None, on_stop=None,
                 on_bootstrap=None, on_setup=None, **kwargs):
        super().__init__(
            parent, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
            **kwargs,
        )
        self._on_launch = on_launch
        self._on_stop = on_stop
        self._on_bootstrap = on_bootstrap
        self._on_setup = on_setup

        # Header row
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=32)
        hdr.pack(fill="x", padx=20, pady=(14, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="Emulator",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_DIM,
        ).pack(side="right")

        self._dot = ctk.CTkFrame(
            hdr, width=10, height=10, corner_radius=5, fg_color=COLOR_ERROR,
        )
        self._dot.pack(side="left", pady=11)
        self._dot.pack_propagate(False)

        self._status = ctk.CTkLabel(
            hdr, text="Stopped",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM,
        )
        self._status.pack(side="left", padx=(10, 0))

        # Info label
        self._info = ctk.CTkLabel(
            self, text="iPhone 11 (A13) · Inferno/QEMU",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_DIM,
        )
        self._info.pack(padx=20, pady=(8, 4), anchor="w")

        # Launch / Stop row
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(4, 4))

        self._launch_btn = ctk.CTkButton(
            row, text="Launch Emulator",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT_BRIGHT,
            height=42, corner_radius=12, border_width=0,
            command=lambda: on_launch and on_launch(),
        )
        self._launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._stop_btn = ctk.CTkButton(
            row, text="Stop",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_ERROR,
            text_color=COLOR_TEXT_DIM,
            height=42, width=70, corner_radius=12,
            command=lambda: on_stop and on_stop(),
            state="disabled",
        )
        self._stop_btn.pack(side="right")

        # Install Sileo / Setup row
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(2, 14))

        self._bootstrap_btn = ctk.CTkButton(
            row2, text="Install Sileo",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT_DIM,
            height=32, corner_radius=10, border_width=0,
            command=lambda: on_bootstrap and on_bootstrap(),
        )
        self._bootstrap_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._setup_btn = ctk.CTkButton(
            row2, text="Setup Wizard",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_DIM,
            height=32, corner_radius=10, border_width=0,
            command=lambda: on_setup and on_setup(),
        )
        self._setup_btn.pack(side="right")

    # Public API

    def set_launching(self):
        self._dot.configure(fg_color=COLOR_WARNING)
        self._status.configure(text="Starting...")
        self._launch_btn.configure(state="disabled", text="Starting...")
        self._stop_btn.configure(state="normal")
        self._bootstrap_btn.configure(state="disabled")

    def set_running(self):
        self._dot.configure(fg_color=COLOR_SUCCESS)
        self._status.configure(text="Running")
        self._launch_btn.configure(state="disabled", text="Running")
        self._stop_btn.configure(state="normal")
        self._bootstrap_btn.configure(state="disabled")

    def set_stopped(self):
        self._dot.configure(fg_color=COLOR_ERROR)
        self._status.configure(text="Stopped")
        self._launch_btn.configure(state="normal", text="Launch Emulator")
        self._stop_btn.configure(state="disabled")
        self._bootstrap_btn.configure(state="normal")

    def set_error(self, msg="Error"):
        self._dot.configure(fg_color=COLOR_ERROR)
        self._status.configure(text=msg)
        self._launch_btn.configure(state="normal", text="Retry")
        self._stop_btn.configure(state="disabled")
        self._bootstrap_btn.configure(state="normal")

    def set_bootstrap_running(self):
        self._bootstrap_btn.configure(
            state="disabled", text="Installing Sileo...",
            fg_color=COLOR_WARNING, text_color=COLOR_TEXT_BRIGHT,
        )

    def set_bootstrap_done(self, success=True):
        if success:
            self._bootstrap_btn.configure(
                state="normal", text="Sileo Installed",
                fg_color=COLOR_SUCCESS, text_color="#050510",
            )
        else:
            self._bootstrap_btn.configure(
                state="normal", text="Install Sileo (Retry)",
                fg_color=COLOR_GLASS_LIGHT, text_color=COLOR_TEXT_DIM,
            )
