"""
Liquid glass real-time console log panel.
"""

import datetime
import customtkinter as ctk

from config.constants import (
    COLOR_GLASS,
    COLOR_GLASS_BORDER,
    COLOR_GLASS_LIGHT,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_INFO,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
)

_COLORS = {"info": COLOR_INFO, "success": COLOR_SUCCESS, "warning": COLOR_WARNING, "error": COLOR_ERROR}
_PREFIX = {"info": "INFO", "success": " OK ", "warning": "WARN", "error": " ERR"}


class LogPanel(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
            **kwargs,
        )

        # Header row
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=34)
        hdr.pack(fill="x", padx=18, pady=(14, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="Console",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_DIM,
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="Clear", width=56, height=26,
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM, corner_radius=8, border_width=0,
            command=self.clear,
        ).pack(side="right")

        # Text area
        self._tb = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=COLOR_GLASS_LIGHT, text_color=COLOR_TEXT,
            corner_radius=12,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
            wrap="word", state="disabled", activate_scrollbars=True,
        )
        self._tb.pack(fill="both", expand=True, padx=12, pady=12)

        for lvl, col in _COLORS.items():
            self._tb._textbox.tag_configure(lvl, foreground=col)
        self._tb._textbox.tag_configure("ts", foreground=COLOR_TEXT_DIM)

    def log(self, level, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        pfx = _PREFIX.get(level, "INFO")
        self._tb.configure(state="normal")
        self._tb._textbox.insert("end", f"[{ts}] ", "ts")
        self._tb._textbox.insert("end", f"[{pfx}] ", level)
        self._tb._textbox.insert("end", f"{message}\n", level)
        self._tb.configure(state="disabled")
        self._tb._textbox.see("end")

    def clear(self):
        self._tb.configure(state="normal")
        self._tb._textbox.delete("1.0", "end")
        self._tb.configure(state="disabled")

    def log_separator(self):
        self._tb.configure(state="normal")
        self._tb._textbox.insert("end", f"{'─' * 50}\n", "ts")
        self._tb.configure(state="disabled")
        self._tb._textbox.see("end")
