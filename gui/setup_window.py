# -*- coding: utf-8 -*-
"""
Inferno emulator setup wizard window.

Opens as a CTkToplevel with a step list on the left and a
detail/log area on the right, following the liquid glass style.
"""

import datetime
import queue
import threading
import customtkinter as ctk

from config.constants import (
    COLOR_BG,
    COLOR_GLASS,
    COLOR_GLASS_LIGHT,
    COLOR_GLASS_BORDER,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT,
    GLASS_RADIUS,
    GLASS_BORDER_WIDTH,
    WIZARD_WIDTH,
    WIZARD_HEIGHT,
)
from config.setup_steps import detect_platform, get_steps_for_platform, SETUP_STEPS
from core.setup_engine import SetupEngine

_STATUS_SYMBOLS = {
    "pending": "\u25cb",   # ○
    "running": "\u25cf",   # ●
    "done": "\u2713",      # ✓
    "failed": "\u2717",    # ✗
    "skipped": "\u2014",   # —
    "manual": "\u25c9",    # ◉
}

_STATUS_COLORS = {
    "pending": COLOR_TEXT_DIM,
    "running": COLOR_WARNING,
    "done": COLOR_SUCCESS,
    "failed": COLOR_ERROR,
    "skipped": COLOR_TEXT_DIM,
    "manual": COLOR_INFO,
}

_LOG_COLORS = {
    "info": COLOR_INFO,
    "success": COLOR_SUCCESS,
    "warning": COLOR_WARNING,
    "error": COLOR_ERROR,
}
_LOG_PREFIX = {"info": "INFO", "success": " OK ", "warning": "WARN", "error": " ERR"}

_PLATFORM_LABELS = {
    "windows": "Windows (WSL)",
    "macos": "macOS",
    "linux": "Linux",
}


class SetupWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Inferno Setup Wizard")
        self.geometry(f"{WIZARD_WIDTH}x{WIZARD_HEIGHT}")
        self.minsize(700, 500)
        self.configure(fg_color=COLOR_BG)

        self._platform = detect_platform()
        self._steps = get_steps_for_platform(self._platform)
        self._step_status = {s["id"]: "manual" if not s.get("automated") else "pending"
                             for s in self._steps}
        self._selected_step = self._steps[0]["id"] if self._steps else None
        self._engine = None
        self._worker_thread = None
        self._log_queue = queue.Queue()
        self._step_queue = queue.Queue()

        # Default work dir
        if self._platform == "windows":
            self._work_dir = "$HOME/InfernoData"
        else:
            import os
            self._work_dir = os.path.expanduser("~/InfernoData")

        self._build_ui()
        self._poll_queues()
        self._select_step(self._steps[0]["id"] if self._steps else None)

    # ── UI construction ─────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
                           border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER)
        hdr.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(hdr, text="Inferno Setup Wizard",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLOR_ACCENT).pack(side="left", padx=18, pady=12)

        ctk.CTkLabel(hdr, text=_PLATFORM_LABELS.get(self._platform, self._platform),
                     font=ctk.CTkFont(size=12),
                     text_color=COLOR_TEXT_DIM).pack(side="right", padx=18)

        # Main body: two-column
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=6)

        # Left: step list
        left = ctk.CTkFrame(body, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
                            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
                            width=260)
        left.pack(side="left", fill="y", padx=(0, 6))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Steps",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLOR_TEXT_DIM).pack(padx=14, pady=(12, 6), anchor="w")

        self._step_frame = ctk.CTkScrollableFrame(
            left, fg_color="transparent",
            scrollbar_button_color=COLOR_GLASS_LIGHT,
            scrollbar_button_hover_color=COLOR_GLASS_BORDER,
        )
        self._step_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._step_rows = {}
        for i, step in enumerate(self._steps):
            self._make_step_row(step, i)

        # Work dir entry
        dir_frame = ctk.CTkFrame(left, fg_color="transparent")
        dir_frame.pack(fill="x", padx=10, pady=(2, 10))

        ctk.CTkLabel(dir_frame, text="Work dir:",
                     font=ctk.CTkFont(size=10),
                     text_color=COLOR_TEXT_DIM).pack(anchor="w")

        self._dir_entry = ctk.CTkEntry(
            dir_frame, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLOR_GLASS_LIGHT, border_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT, height=28, corner_radius=8,
        )
        self._dir_entry.pack(fill="x")
        self._dir_entry.insert(0, self._work_dir)

        # Right: detail + log + buttons
        right = ctk.CTkFrame(body, fg_color=COLOR_GLASS, corner_radius=GLASS_RADIUS,
                             border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER)
        right.pack(side="right", fill="both", expand=True)

        # Detail area
        self._detail_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._detail_frame.pack(fill="x", padx=14, pady=(12, 0))

        self._detail_name = ctk.CTkLabel(
            self._detail_frame, text="",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=COLOR_TEXT,
        )
        self._detail_name.pack(anchor="w")

        self._detail_desc = ctk.CTkLabel(
            self._detail_frame, text="",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM,
            wraplength=500, justify="left", anchor="w",
        )
        self._detail_desc.pack(anchor="w", pady=(4, 0))

        # Manual instructions area (hidden by default)
        self._manual_frame = ctk.CTkFrame(right, fg_color=COLOR_GLASS_LIGHT,
                                          corner_radius=10)

        self._manual_text = ctk.CTkLabel(
            self._manual_frame, text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXT_DIM, wraplength=480,
            justify="left", anchor="nw",
        )
        self._manual_text.pack(padx=12, pady=10, anchor="w")

        # Log area
        self._log_tb = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLOR_GLASS_LIGHT, text_color=COLOR_TEXT,
            corner_radius=10,
            border_width=GLASS_BORDER_WIDTH, border_color=COLOR_GLASS_BORDER,
            wrap="word", state="disabled", activate_scrollbars=True,
        )
        self._log_tb.pack(fill="both", expand=True, padx=10, pady=8)

        for lvl, col in _LOG_COLORS.items():
            self._log_tb._textbox.tag_configure(lvl, foreground=col)
        self._log_tb._textbox.tag_configure("ts", foreground=COLOR_TEXT_DIM)

        # Buttons
        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))

        self._run_btn = ctk.CTkButton(
            btn_row, text="Run Step",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT_BRIGHT, height=40, corner_radius=10,
            command=self._on_run_step,
        )
        self._run_btn.pack(side="left", padx=(0, 6))

        self._skip_btn = ctk.CTkButton(
            btn_row, text="Skip",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM, height=40, width=70, corner_radius=10,
            command=self._on_skip_step,
        )
        self._skip_btn.pack(side="left", padx=(0, 6))

        self._cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_ERROR,
            text_color=COLOR_TEXT_DIM, height=40, width=70, corner_radius=10,
            command=self._on_cancel,
            state="disabled",
        )
        self._cancel_btn.pack(side="left")

        ctk.CTkButton(
            btn_row, text="Close",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_LIGHT, hover_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_DIM, height=40, width=70, corner_radius=10,
            command=self.destroy,
        ).pack(side="right")

    # ── Step list rows ──────────────────────────────────────────

    def _make_step_row(self, step, index):
        sid = step["id"]
        status = self._step_status[sid]

        row = ctk.CTkFrame(self._step_frame, fg_color="transparent",
                           height=32, cursor="hand2")
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        sym_label = ctk.CTkLabel(
            row, text=_STATUS_SYMBOLS[status], width=22,
            font=ctk.CTkFont(size=13),
            text_color=_STATUS_COLORS[status],
        )
        sym_label.pack(side="left", padx=(6, 4))

        num_label = ctk.CTkLabel(
            row, text=f"{index + 1}.",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_DIM, width=22,
        )
        num_label.pack(side="left")

        name_label = ctk.CTkLabel(
            row, text=step["name"],
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT, anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True)

        self._step_rows[sid] = {
            "row": row, "sym": sym_label, "name": name_label,
        }

        # Click handler
        for widget in (row, sym_label, num_label, name_label):
            widget.bind("<Button-1>", lambda e, s=sid: self._select_step(s))

    def _update_step_row(self, step_id, status):
        self._step_status[step_id] = status
        row_data = self._step_rows.get(step_id)
        if row_data:
            row_data["sym"].configure(
                text=_STATUS_SYMBOLS.get(status, "?"),
                text_color=_STATUS_COLORS.get(status, COLOR_TEXT_DIM),
            )

    # ── Step selection ──────────────────────────────────────────

    def _select_step(self, step_id):
        if step_id is None:
            return
        self._selected_step = step_id

        # Highlight selected row
        for sid, rd in self._step_rows.items():
            rd["row"].configure(fg_color=COLOR_GLASS_LIGHT if sid == step_id
                                else "transparent")

        # Find step data
        step = next((s for s in self._steps if s["id"] == step_id), None)
        if not step:
            return

        self._detail_name.configure(text=step["name"])
        self._detail_desc.configure(text=step["description"])

        # Show/hide manual instructions
        is_manual = not step.get("automated", False)
        instructions = step.get("manual_instructions", "")

        if is_manual and instructions:
            self._manual_text.configure(text=instructions)
            self._manual_frame.pack(fill="x", padx=14, pady=(6, 0),
                                    after=self._detail_frame)
        else:
            self._manual_frame.pack_forget()

        # Update buttons
        is_running = (self._worker_thread and self._worker_thread.is_alive())
        status = self._step_status.get(step_id, "pending")

        if is_running:
            self._run_btn.configure(state="disabled")
            self._skip_btn.configure(state="disabled")
            self._cancel_btn.configure(state="normal")
        elif is_manual:
            self._run_btn.configure(state="disabled", text="Manual Step")
            self._skip_btn.configure(state="normal")
            self._cancel_btn.configure(state="disabled")
        else:
            self._run_btn.configure(state="normal", text="Run Step")
            self._skip_btn.configure(state="normal")
            self._cancel_btn.configure(state="disabled")

    # ── Actions ─────────────────────────────────────────────────

    def _on_run_step(self):
        if not self._selected_step:
            return
        if self._worker_thread and self._worker_thread.is_alive():
            return

        step = next((s for s in self._steps if s["id"] == self._selected_step), None)
        if not step or not step.get("automated"):
            return

        # Read work dir from entry
        self._work_dir = self._dir_entry.get().strip() or self._work_dir

        # Clear log
        self._log_tb.configure(state="normal")
        self._log_tb._textbox.delete("1.0", "end")
        self._log_tb.configure(state="disabled")

        # Update UI
        self._run_btn.configure(state="disabled", text="Running...")
        self._skip_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")

        self._engine = SetupEngine(
            self._platform, self._work_dir,
            log_callback=self._log_t,
            step_callback=self._step_t,
        )

        step_id = self._selected_step
        self._worker_thread = threading.Thread(
            target=self._run_worker, args=(step_id,), daemon=True,
        )
        self._worker_thread.start()

    def _run_worker(self, step_id):
        self._engine.run_step(step_id)

    def _on_skip_step(self):
        if not self._selected_step:
            return
        self._update_step_row(self._selected_step, "skipped")
        # Advance to next step
        self._advance_selection()

    def _on_cancel(self):
        if self._engine:
            self._engine.cancel()

    def _advance_selection(self):
        """Select the next pending/manual step after current."""
        ids = [s["id"] for s in self._steps]
        try:
            idx = ids.index(self._selected_step)
        except ValueError:
            return
        for i in range(idx + 1, len(ids)):
            status = self._step_status.get(ids[i])
            if status in ("pending", "manual", "failed"):
                self._select_step(ids[i])
                return

    # ── Thread-safe queue communication ─────────────────────────

    def _log_t(self, level, msg):
        self._log_queue.put((level, msg))

    def _step_t(self, step_id, status):
        self._step_queue.put((step_id, status))

    def _poll_queues(self):
        try:
            while True:
                level, msg = self._log_queue.get_nowait()
                self._append_log(level, msg)
        except queue.Empty:
            pass
        try:
            while True:
                step_id, status = self._step_queue.get_nowait()
                self._update_step_row(step_id, status)
                if status in ("done", "failed"):
                    self._on_step_finished(step_id, status)
        except queue.Empty:
            pass
        self.after(50, self._poll_queues)

    def _append_log(self, level, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        pfx = _LOG_PREFIX.get(level, "INFO")
        self._log_tb.configure(state="normal")
        self._log_tb._textbox.insert("end", f"[{ts}] ", "ts")
        self._log_tb._textbox.insert("end", f"[{pfx}] ", level)
        self._log_tb._textbox.insert("end", f"{message}\n", level)
        self._log_tb.configure(state="disabled")
        self._log_tb._textbox.see("end")

    def _on_step_finished(self, step_id, status):
        self._cancel_btn.configure(state="disabled")
        if status == "done":
            self._run_btn.configure(text="Done!", state="disabled")
            self._advance_selection()
        else:
            self._run_btn.configure(text="Retry", state="normal")
        self._skip_btn.configure(state="normal")
