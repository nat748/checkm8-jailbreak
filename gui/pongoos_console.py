"""
pongoOS console window.

Shows real-time output from the pongoOS serial console.
"""

import customtkinter as ctk
from typing import Callable, Optional

from config.constants import (
    COLOR_BG,
    COLOR_GLASS,
    COLOR_GLASS_LIGHT,
    COLOR_GLASS_BORDER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    COLOR_ACCENT,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
)


class PongoOSConsole(ctk.CTkToplevel):
    """Console window for pongoOS."""

    def __init__(self, parent, on_send_command: Optional[Callable] = None):
        """
        Initialize console window.

        Args:
            parent: Parent window
            on_send_command: Callback for sending commands to pongoOS
        """
        super().__init__(parent)

        self._on_send_command = on_send_command

        # Window configuration
        self.title("pongoOS Console")
        self.geometry("700x500")
        self.minsize(500, 300)
        self.configure(fg_color=COLOR_BG)

        # Make it float on top
        self.attributes('-topmost', False)

        # Main container
        container = ctk.CTkFrame(
            self,
            fg_color=COLOR_GLASS,
            border_width=GLASS_BORDER_WIDTH,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=GLASS_RADIUS,
        )
        container.pack(fill="both", expand=True, padx=14, pady=14)

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text="pongoOS Serial Console",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_BRIGHT,
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Clear",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_GLASS_LIGHT,
            hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM,
            width=60,
            height=28,
            corner_radius=8,
            command=self._clear_console,
        ).pack(side="right")

        # Console output area (scrollable textbox)
        self._console = ctk.CTkTextbox(
            container,
            fg_color=COLOR_BG,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
        )
        self._console.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Welcome message
        self._console.insert("1.0", "pongoOS Console - Waiting for output...\n")
        self._console.insert("end", "=" * 60 + "\n\n")
        self._console.configure(state="disabled")

        # Command input area
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            input_frame,
            text=">",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLOR_ACCENT,
        ).pack(side="left", padx=(0, 8))

        self._command_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter pongoOS command (e.g., help, bootx)",
            fg_color=COLOR_GLASS_LIGHT,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self._command_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._command_entry.bind("<Return>", lambda e: self._send_command())

        ctk.CTkButton(
            input_frame,
            text="Send",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_ACCENT,
            hover_color="#9b6dff",
            text_color="white",
            width=70,
            height=32,
            corner_radius=8,
            command=self._send_command,
        ).pack(side="left")

        # Auto-scroll enabled by default
        self._auto_scroll = True

    def append_output(self, text: str):
        """
        Append text to console output.

        Args:
            text: Text to append
        """
        self._console.configure(state="normal")
        self._console.insert("end", text)
        if self._auto_scroll:
            self._console.see("end")
        self._console.configure(state="disabled")

    def _clear_console(self):
        """Clear console output."""
        self._console.configure(state="normal")
        self._console.delete("1.0", "end")
        self._console.insert("1.0", "Console cleared\n" + "=" * 60 + "\n\n")
        self._console.configure(state="disabled")

    def _send_command(self):
        """Send command to pongoOS."""
        command = self._command_entry.get().strip()
        if not command:
            return

        # Display command in console
        self._console.configure(state="normal")
        self._console.insert("end", f"> {command}\n", "command")
        self._console.configure(state="disabled")

        # Send to pongoOS
        if self._on_send_command:
            self._on_send_command(command)

        # Clear input
        self._command_entry.delete(0, "end")
