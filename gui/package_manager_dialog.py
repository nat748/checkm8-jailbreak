"""
Package manager selection dialog.

Allows user to choose between Zebra, Sileo, or Cydia before installation.
"""

import customtkinter as ctk

from config.constants import (
    COLOR_BG,
    COLOR_GLASS_DARK,
    COLOR_GLASS_LIGHT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_PRIMARY,
    COLOR_ACCENT,
)


class PackageManagerDialog(ctk.CTkToplevel):
    """Modal dialog for selecting package manager."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Choose Package Manager")
        self.geometry("500x400")
        self.resizable(False, False)

        # Glass styling
        self.configure(fg_color=COLOR_BG)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        self._selected = None
        self._create_ui()

    def _create_ui(self):
        """Build the dialog UI."""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color=COLOR_GLASS_DARK, corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            container,
            text="Select Package Manager",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        title.pack(pady=(20, 10))

        # Description
        desc = ctk.CTkLabel(
            container,
            text="Choose which package manager to install on the Inferno emulator.\n"
                 "This will be used to install jailbreak tweaks and apps.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_DIM,
            justify="center",
        )
        desc.pack(pady=(0, 20))

        # Package manager options
        options_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Sileo (recommended)
        self._create_option(
            options_frame,
            "Sileo",
            "Modern APT frontend with smooth UI\n"
            "Official checkra1n bootstrap\n"
            "✓ Recommended for best compatibility",
            "sileo",
            0,
            recommended=True,
        )

        # Zebra
        self._create_option(
            options_frame,
            "Zebra",
            "Lightweight and fast package manager\n"
            "Clean interface, good performance\n"
            "Community-maintained",
            "zebra",
            1,
        )

        # Cydia
        self._create_option(
            options_frame,
            "Cydia",
            "Classic jailbreak package manager\n"
            "Most compatible with legacy repos\n"
            "Slower but battle-tested",
            "cydia",
            2,
        )

    def _create_option(self, parent, name, description, value, row, recommended=False):
        """Create a package manager option button."""
        btn = ctk.CTkButton(
            parent,
            text=f"{'★ ' if recommended else ''}{name}",
            font=ctk.CTkFont(size=14, weight="bold" if recommended else "normal"),
            fg_color=COLOR_GLASS_LIGHT if not recommended else COLOR_ACCENT,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_PRIMARY,
            height=80,
            corner_radius=10,
            command=lambda: self._on_select(value),
        )
        btn.grid(row=row, column=0, sticky="ew", pady=5)

        desc_label = ctk.CTkLabel(
            parent,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_DIM,
            justify="left",
            anchor="w",
        )
        desc_label.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=5)

        parent.grid_columnconfigure(0, weight=0, minsize=150)
        parent.grid_columnconfigure(1, weight=1)

    def _on_select(self, value):
        """Handle package manager selection."""
        self._selected = value
        self.grab_release()
        self.destroy()

    def get_selection(self):
        """Return the selected package manager (or None if cancelled)."""
        self.wait_window()
        return self._selected
