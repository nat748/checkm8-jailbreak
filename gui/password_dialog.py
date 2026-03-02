"""
Password entry dialog for sudo operations.

Shows a secure password field and validates before returning.
"""

import customtkinter as ctk

from config.constants import (
    COLOR_BG,
    COLOR_GLASS,
    COLOR_GLASS_LIGHT,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    COLOR_ACCENT,
    COLOR_ERROR,
)


class PasswordDialog(ctk.CTkToplevel):
    """Modal dialog for entering sudo password."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sudo Password Required")
        self.geometry("450x250")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Center on parent
        self.transient(parent)
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 250) // 2
        self.geometry(f"+{x}+{y}")

        # Modal
        self.grab_set()

        self._password = None
        self._create_ui()

    def _create_ui(self):
        """Build the dialog UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color=COLOR_GLASS, corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            container,
            text="🔐 Sudo Password",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_BRIGHT,
        )
        title.pack(pady=(20, 10))

        # Description
        desc = ctk.CTkLabel(
            container,
            text="This setup requires sudo access to mount disk images\n"
                 "and install system packages. Your password will be\n"
                 "used only for this session and not stored.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_DIM,
            justify="center",
        )
        desc.pack(pady=(0, 20))

        # Password entry
        self._entry = ctk.CTkEntry(
            container,
            width=300,
            height=40,
            placeholder_text="Enter your password",
            show="●",
            font=ctk.CTkFont(size=14),
            fg_color=COLOR_GLASS_LIGHT,
            text_color=COLOR_TEXT,
            border_color=COLOR_ACCENT,
            border_width=2,
        )
        self._entry.pack(pady=10)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda e: self._on_ok())

        # Error label (hidden by default)
        self._error_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_ERROR,
        )
        self._error_label.pack(pady=(5, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(pady=(15, 10))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT,
            hover_color=COLOR_ACCENT,
            text_color=COLOR_TEXT_DIM,
            width=120,
            height=36,
            corner_radius=10,
            command=self._on_cancel,
        )
        cancel_btn.pack(side="left", padx=5)

        ok_btn = ctk.CTkButton(
            btn_frame,
            text="OK",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_GLASS_LIGHT,
            text_color=COLOR_TEXT_BRIGHT,
            width=120,
            height=36,
            corner_radius=10,
            command=self._on_ok,
        )
        ok_btn.pack(side="left", padx=5)

    def _on_ok(self):
        """Validate and return password."""
        pwd = self._entry.get()
        if not pwd:
            self._error_label.configure(text="Password cannot be empty")
            return

        self._password = pwd
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        """Cancel without returning password."""
        self._password = None
        self.grab_release()
        self.destroy()

    def get_password(self):
        """Get the entered password (None if cancelled)."""
        self.wait_window()
        return self._password
