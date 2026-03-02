"""
Update notification dialog for checkm8.

Shows when a new version is available.
"""

import customtkinter as ctk
import webbrowser
from typing import Optional
from config.constants import (
    COLOR_BG_DARK, COLOR_GLASS_LIGHT, COLOR_GLASS_BORDER,
    COLOR_TEXT_BRIGHT, COLOR_TEXT_DIM, COLOR_ACCENT
)


class UpdateDialog(ctk.CTkToplevel):
    """Dialog showing available update."""

    def __init__(self, parent, release_info: dict):
        """
        Initialize update dialog.

        Args:
            parent: Parent window
            release_info: Dict with version, url, notes, assets
        """
        super().__init__(parent)

        self._release_info = release_info

        # Window configuration
        self.title("Update Available")
        self.geometry("500x400")
        self.resizable(False, False)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Styling
        self.configure(fg_color=COLOR_BG_DARK)

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        # Main container with glass effect
        container = ctk.CTkFrame(
            self,
            fg_color=COLOR_GLASS_LIGHT,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=15
        )
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(
            container,
            text="🎉 New Version Available!",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXT_BRIGHT
        )
        header.pack(pady=(20, 10))

        # Version info
        version_text = f"Version {self._release_info['version']} is now available"
        version_label = ctk.CTkLabel(
            container,
            text=version_text,
            font=ctk.CTkFont(size=14),
            text_color=COLOR_TEXT_DIM
        )
        version_label.pack(pady=(0, 20))

        # Release notes (scrollable)
        notes_label = ctk.CTkLabel(
            container,
            text="What's New:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_BRIGHT
        )
        notes_label.pack(anchor="w", padx=20)

        notes_box = ctk.CTkTextbox(
            container,
            width=440,
            height=180,
            fg_color=COLOR_BG_DARK,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        notes_box.pack(padx=20, pady=(5, 15))

        # Insert release notes
        notes = self._release_info.get('notes', 'No release notes available.')
        notes_box.insert("1.0", notes)
        notes_box.configure(state="disabled")

        # Download files info
        assets = self._release_info.get('assets', [])
        if assets:
            files_label = ctk.CTkLabel(
                container,
                text=f"Available downloads: {len(assets)} file(s)",
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_DIM
            )
            files_label.pack(pady=(0, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        # Download button
        download_btn = ctk.CTkButton(
            btn_frame,
            text="Download Update",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color="#9b6dff",
            text_color="white",
            width=180,
            height=40,
            corner_radius=10,
            command=self._on_download
        )
        download_btn.pack(side="left", padx=5)

        # Remind later button
        later_btn = ctk.CTkButton(
            btn_frame,
            text="Remind Me Later",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT,
            hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            width=150,
            height=40,
            corner_radius=10,
            command=self._on_later
        )
        later_btn.pack(side="left", padx=5)

    def _on_download(self):
        """Open download page in browser."""
        url = self._release_info.get('url', '')
        if url:
            webbrowser.open(url)
        self.destroy()

    def _on_later(self):
        """Close dialog without downloading."""
        self.destroy()


def show_update_dialog(parent, release_info: dict) -> Optional[UpdateDialog]:
    """
    Show update notification dialog.

    Args:
        parent: Parent window
        release_info: Release information dict

    Returns:
        UpdateDialog instance or None if dialog couldn't be created
    """
    try:
        return UpdateDialog(parent, release_info)
    except Exception as e:
        print(f"Failed to show update dialog: {e}")
        return None
