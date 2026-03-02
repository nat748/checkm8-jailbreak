"""
Smooth animated fluid background.

Renders all gradient blobs into a single PIL image at low resolution,
then scales up for a naturally smooth, blurred look (like Apple's
liquid glass wallpapers). Displayed as one canvas image, updated at 20fps.

The low-res render + bilinear upscale eliminates any hard edges,
producing a seamless flowing gradient.
"""

import math
import time
import random
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter, ImageTk

from config.constants import COLOR_BG, BLOB_COLORS

# Render at this fraction of display size for smooth blur
RENDER_SCALE = 0.20
FRAME_MS = 200  # 5 fps — keeps CPU free for the emulator
BG_RGB = (8, 8, 26)


def _make_blob(size, color, alpha):
    """Pre-render a soft radial gradient circle at render scale."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r, g, b = color
    cx = size // 2
    for i in range(cx, 0, -2):
        ratio = i / cx
        a = int(alpha * ratio ** 2.8)
        draw.ellipse([cx - i, cx - i, cx + i, cx + i], fill=(r, g, b, a))
    img = img.filter(ImageFilter.GaussianBlur(radius=max(2, size // 3)))
    return img


class _Blob:
    """Parameters for one animated blob."""

    def __init__(self, img, bx, by, sx, sy, phase):
        self.img = img
        self.half = img.width // 2
        self.bx = bx
        self.by = by
        self.sx = sx
        self.sy = sy
        self.phase = phase
        self.ax = random.uniform(0.07, 0.14)
        self.ay = random.uniform(0.05, 0.11)

    def pos(self, t, rw, rh):
        x = (self.bx + math.sin(t * self.sx + self.phase) * self.ax) * rw
        y = (self.by + math.cos(t * self.sy + self.phase * 1.3) * self.ay) * rh
        return int(x) - self.half, int(y) - self.half


# Blob definitions: (display_size, color_index, base_x%, base_y%, spd_x, spd_y, phase, alpha)
_BLOB_DEFS = [
    (600, 0, 0.20, 0.25, 0.22, 0.16, 0.0, 170),
    (700, 1, 0.65, 0.35, 0.16, 0.24, 1.0, 150),
    (500, 2, 0.82, 0.18, 0.20, 0.14, 2.0, 140),
    (550, 3, 0.30, 0.70, 0.26, 0.18, 3.0, 120),
    (650, 4, 0.08, 0.60, 0.14, 0.20, 4.0, 140),
    (400, 5, 0.50, 0.12, 0.18, 0.22, 5.0, 100),
]


class FluidBackground:
    """
    Composites all blobs into a single smooth image per frame.

    Renders at RENDER_SCALE (25%), then bilinear-upscales to full size.
    The upscale acts as extra blur, producing an Apple-like flowing gradient.
    """

    def __init__(self, canvas):
        self.canvas = canvas
        self.canvas.configure(bg=COLOR_BG)

        # Get display dimensions from canvas
        self._display_w = 1200
        self._display_h = 820

        self._blobs = []
        for disp_size, ci, bx, by, sx, sy, phase, alpha in _BLOB_DEFS:
            rs = max(8, int(disp_size * RENDER_SCALE))
            color = BLOB_COLORS[ci]
            img = _make_blob(rs, color, alpha)
            self._blobs.append(_Blob(img, bx, by, sx, sy, phase))

        self._photo = None
        self._img_id = canvas.create_image(0, 0, anchor="nw")

        self._running = False
        self._t0 = 0.0

        # Render first frame immediately
        self._render_and_display(0.0)

        # Track canvas size changes (lightweight - just stores new dims)
        canvas.bind("<Configure>", self._on_configure, add=True)

    def _on_configure(self, event):
        self._display_w = max(100, event.width)
        self._display_h = max(100, event.height)

    def _render_and_display(self, t):
        dw, dh = self._display_w, self._display_h
        rw = max(4, int(dw * RENDER_SCALE))
        rh = max(4, int(dh * RENDER_SCALE))

        frame = Image.new("RGB", (rw, rh), BG_RGB)

        for blob in self._blobs:
            px, py = blob.pos(t, rw, rh)
            # Only paste if blob overlaps the frame
            if (px + blob.img.width > 0 and py + blob.img.height > 0
                    and px < rw and py < rh):
                frame.paste(blob.img, (px, py), blob.img)

        # Upscale: bilinear naturally blurs everything smooth
        frame = frame.resize((dw, dh), Image.BILINEAR)

        self._photo = ImageTk.PhotoImage(frame)
        self.canvas.itemconfigure(self._img_id, image=self._photo)

    def start(self):
        self._running = True
        self._t0 = time.time()
        self._tick()

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        t = time.time() - self._t0
        self._render_and_display(t)
        self.canvas.after(FRAME_MS, self._tick)
