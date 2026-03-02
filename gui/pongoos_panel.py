"""
pongoOS emulator control panel.
"""

import customtkinter as ctk
from typing import Optional, Callable

from config.constants import (
    COLOR_GLASS,
    COLOR_GLASS_LIGHT,
    COLOR_GLASS_BORDER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
)


class PongoOSPanel(ctk.CTkFrame):
    """Panel for pongoOS emulator control."""

    def __init__(
        self,
        parent,
        on_launch: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_setup: Optional[Callable] = None,
        on_console: Optional[Callable] = None,
    ):
        """
        Initialize pongoOS panel.

        Args:
            parent: Parent widget
            on_launch: Callback for launch button
            on_stop: Callback for stop button
            on_setup: Callback for setup wizard
            on_console: Callback for console window
        """
        super().__init__(
            parent,
            fg_color=COLOR_GLASS,
            corner_radius=GLASS_RADIUS,
            border_width=GLASS_BORDER_WIDTH,
            border_color=COLOR_GLASS_BORDER,
        )

        self._on_launch = on_launch
        self._on_stop = on_stop
        self._on_setup = on_setup
        self._on_console = on_console

        # Title
        ctk.CTkLabel(
            self,
            text="pongoOS Emulator",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_BRIGHT,
        ).pack(padx=18, pady=(14, 2), anchor="w")

        # Status label
        self._status_label = ctk.CTkLabel(
            self,
            text="Ready to launch",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_DIM,
        )
        self._status_label.pack(padx=18, pady=(0, 12), anchor="w")

        # Info label
        self._info_label = ctk.CTkLabel(
            self,
            text="QEMU ARM64 virtual device with pongoOS",
            font=ctk.CTkFont(size=10),
            text_color=COLOR_TEXT_DIM,
            wraplength=260,
            justify="left",
        )
        self._info_label.pack(padx=18, pady=(0, 12), anchor="w")

        # Button row 1: Launch / Stop
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 8))

        self._launch_btn = ctk.CTkButton(
            row1,
            text="Launch Emulator",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_ACCENT,
            hover_color="#9b6dff",
            text_color="white",
            height=36,
            corner_radius=10,
            command=lambda: on_launch and on_launch(),
        )
        self._launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._stop_btn = ctk.CTkButton(
            row1,
            text="Stop",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_GLASS_LIGHT,
            hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM,
            height=36,
            corner_radius=10,
            state="disabled",
            command=lambda: on_stop and on_stop(),
        )
        self._stop_btn.pack(side="left", padx=(4, 0))

        # Button row 2: Setup / Console
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        self._setup_btn = ctk.CTkButton(
            row2,
            text="Setup pongoOS",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_GLASS_LIGHT,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_DIM,
            height=30,
            corner_radius=10,
            command=lambda: on_setup and on_setup(),
        )
        self._setup_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._console_btn = ctk.CTkButton(
            row2,
            text="Console",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_GLASS_LIGHT,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_DIM,
            height=30,
            corner_radius=10,
            state="disabled",
            command=lambda: on_console and on_console(),
        )
        self._console_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

    # ---- State management ----

    def set_launching(self):
        """Set panel to launching state."""
        self._status_label.configure(text="Launching...", text_color=COLOR_ACCENT)
        self._launch_btn.configure(state="disabled")
        self._stop_btn.configure(state="disabled")
        self._setup_btn.configure(state="disabled")
        self._console_btn.configure(state="disabled")

    def set_running(self):
        """Set panel to running state."""
        self._status_label.configure(text="● Running", text_color=COLOR_SUCCESS)
        self._launch_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._setup_btn.configure(state="disabled")
        self._console_btn.configure(state="normal")

    def set_stopped(self):
        """Set panel to stopped state."""
        self._status_label.configure(text="Stopped", text_color=COLOR_TEXT_DIM)
        self._launch_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._setup_btn.configure(state="normal")
        self._console_btn.configure(state="disabled")

    def set_error(self, message: str):
        """
        Set panel to error state.

        Args:
            message: Error message to display
        """
        self._status_label.configure(text=f"Error: {message}", text_color="#ff6b6b")
        self._launch_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._setup_btn.configure(state="normal")
        self._console_btn.configure(state="disabled")
