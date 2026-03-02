# -*- coding: utf-8 -*-
"""
About / credits window.
"""

import webbrowser
import customtkinter as ctk

from config.constants import (
    COLOR_BG,
    COLOR_GLASS,
    COLOR_GLASS_LIGHT,
    COLOR_GLASS_BORDER,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
    APP_NAME,
    APP_VERSION,
)

# (label, url, description)
_CREDITS = [
    (
        "checkm8 Exploit",
        "https://github.com/axi0mX/ipwndfu",
        "axi0mX \u2014 CVE-2019-8900 bootrom exploit for A5\u2013A11 chips",
    ),
    (
        "Inferno (QEMU Fork)",
        "https://github.com/ChefKissInc/Inferno",
        "ChefKissInc \u2014 iPhone 11 (T8030) emulator based on QEMU",
    ),
    (
        "QEMU",
        "https://www.qemu.org/",
        "QEMU contributors \u2014 open-source machine emulator & virtualizer",
    ),
    (
        "checkra1n",
        "https://checkra.in/",
        "checkra1n team \u2014 jailbreak bootstrap, Sileo loader",
    ),
    (
        "img4lib",
        "https://github.com/xerub/img4lib",
        "xerub \u2014 Apple IMG4 parsing and firmware tools",
    ),
    (
        "InfernoFSPatcher",
        "https://git.chefkiss.dev/AppleHax/InfernoFSPatcher",
        "ChefKiss / AppleHax \u2014 dyld shared cache patcher for Inferno",
    ),
    (
        "libimobiledevice",
        "https://libimobiledevice.org/",
        "libimobiledevice project \u2014 iOS device communication libraries",
    ),
    (
        "idevicerestore",
        "https://github.com/libimobiledevice/idevicerestore",
        "libimobiledevice project \u2014 iOS restore utility",
    ),
    (
        "CustomTkinter",
        "https://github.com/TomSchimansky/CustomTkinter",
        "Tom Schimansky \u2014 modern Python UI library",
    ),
    (
        "PyUSB",
        "https://github.com/pyusb/pyusb",
        "PyUSB contributors \u2014 Python USB access library",
    ),
    (
        "Pillow (PIL)",
        "https://python-pillow.org/",
        "Pillow contributors \u2014 image processing for fluid background",
    ),
]


class AboutWindow(ctk.CTkToplevel):

    def __init__(self, parent, on_check_updates=None):
        super().__init__(parent)
        self._on_check_updates = on_check_updates

        self.title("About checkm8")
        self.geometry("560x620")
        self.minsize(460, 400)
        self.configure(fg_color=COLOR_BG)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
                           border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER)
        hdr.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkLabel(
            hdr, text=APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold"), text_color=COLOR_ACCENT,
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            hdr, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=12), text_color=COLOR_TEXT_DIM,
        ).pack()

        ctk.CTkLabel(
            hdr, text="A5\u2013A11 bootrom exploit tool with Inferno emulator integration",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM,
            wraplength=480,
        ).pack(pady=(6, 14))

        # Credits list
        credits_frame = ctk.CTkFrame(self, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
                                     border_width=GLASS_BORDER_WIDTH,
                                     border_color=COLOR_GLASS_BORDER)
        credits_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        ctk.CTkLabel(
            credits_frame, text="Credits & Open Source Licenses",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_DIM,
        ).pack(padx=16, pady=(14, 6), anchor="w")

        scroll = ctk.CTkScrollableFrame(
            credits_frame, fg_color="transparent",
            scrollbar_button_color=COLOR_GLASS_LIGHT,
            scrollbar_button_hover_color=COLOR_GLASS_BORDER,
        )
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        for name, url, desc in _CREDITS:
            self._make_credit_row(scroll, name, url, desc)

        # Disclaimer
        ctk.CTkLabel(
            credits_frame,
            text="This tool is for educational and authorized security research only.",
            font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_DIM,
        ).pack(pady=(0, 12))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 14))

        # Check for updates button (if callback provided)
        if self._on_check_updates:
            ctk.CTkButton(
                btn_frame, text="Check for Updates", height=36, corner_radius=10,
                width=150,
                font=ctk.CTkFont(size=13),
                fg_color=COLOR_ACCENT, hover_color="#9b6dff",
                text_color="white",
                command=self._on_check_updates,
            ).pack(side="left", padx=4)

        # Close button
        ctk.CTkButton(
            btn_frame, text="Close", height=36, corner_radius=10,
            width=100,
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM,
            command=self.destroy,
        ).pack(side="left", padx=4)

    def _make_credit_row(self, parent, name, url, desc):
        row = ctk.CTkFrame(parent, fg_color=COLOR_GLASS_LIGHT, corner_radius=10)
        row.pack(fill="x", pady=3, padx=4)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        link = ctk.CTkLabel(
            inner, text=name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_ACCENT, cursor="hand2",
        )
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

        ctk.CTkLabel(
            inner, text=desc,
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_DIM,
            anchor="w", wraplength=440,
        ).pack(anchor="w", pady=(2, 0))
