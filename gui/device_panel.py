"""
Liquid glass device information panel.
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


class DevicePanel(ctk.CTkFrame):

    def __init__(self, parent, on_detect=None, **kwargs):
        super().__init__(
            parent, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
            **kwargs,
        )
        self._on_detect = on_detect

        # Header row
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=32)
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="Device",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_DIM,
        ).pack(side="right")

        self._dot = ctk.CTkFrame(hdr, width=10, height=10, corner_radius=5, fg_color=COLOR_ERROR)
        self._dot.pack(side="left", pady=11)
        self._dot.pack_propagate(False)

        self._status = ctk.CTkLabel(
            hdr, text="No device",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM,
        )
        self._status.pack(side="left", padx=(10, 0))

        # Fields
        self._fields = {}
        ff = ctk.CTkFrame(self, fg_color="transparent")
        ff.pack(fill="x", padx=20, pady=(10, 4))

        for name in ("Model", "Chip", "ECID"):
            row = ctk.CTkFrame(ff, fg_color="transparent", height=26)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=name,
                font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM,
                width=52, anchor="w",
            ).pack(side="left")

            val = ctk.CTkLabel(
                row, text="—",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=COLOR_TEXT, anchor="w",
            )
            val.pack(side="left", fill="x", expand=True)
            self._fields[name] = val

        # Detect button
        self._btn = ctk.CTkButton(
            self, text="Detect Device",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT_BRIGHT,
            height=42, corner_radius=12, border_width=0,
            command=lambda: on_detect and on_detect(),
        )
        self._btn.pack(fill="x", padx=20, pady=(8, 18))

    def set_detecting(self):
        self._dot.configure(fg_color=COLOR_WARNING)
        self._status.configure(text="Scanning...")
        self._btn.configure(state="disabled", text="Scanning...")
        for v in self._fields.values():
            v.configure(text="...")

    def set_device_info(self, info, config):
        self._dot.configure(fg_color=COLOR_SUCCESS)
        self._status.configure(text="Connected (DFU)")
        self._btn.configure(state="normal", text="Detect Device")
        model = config["devices"][0] if config and config.get("devices") else "Unknown"
        chip = config["name"] if config else f"0x{info.cpid:04X}"
        self._fields["Model"].configure(text=model)
        self._fields["Chip"].configure(text=chip)
        self._fields["ECID"].configure(text=f"0x{info.ecid:016X}")

    def set_not_found(self):
        self._dot.configure(fg_color=COLOR_ERROR)
        self._status.configure(text="Not found")
        self._btn.configure(state="normal", text="Detect Device")
        for v in self._fields.values():
            v.configure(text="—")

    def set_error(self, msg):
        self._dot.configure(fg_color=COLOR_ERROR)
        self._status.configure(text="Error")
        self._btn.configure(state="normal", text="Retry")
