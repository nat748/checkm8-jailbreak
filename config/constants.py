APP_NAME = "checkm8"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1160
WINDOW_HEIGHT = 920

# GitHub repository for updates
# Set these to your own GitHub username and repo name
GITHUB_OWNER = "YOUR_USERNAME"  # Replace with your GitHub username
GITHUB_REPO = "checkm8-jailbreak"  # Replace with your repo name

# Apple USB identifiers
APPLE_VID = 0x05AC
DFU_PID = 0x1227
RECOVERY_PID_RANGE = (0x1280, 0x1290)

# DFU USB constants
DFU_DNLOAD = 1
DFU_UPLOAD = 2
DFU_GET_STATUS = 3
DFU_CLR_STATUS = 4
DFU_GET_STATE = 5
DFU_ABORT = 6

# USB request types
USB_DIR_OUT = 0x00
USB_DIR_IN = 0x80
USB_TYPE_STANDARD = 0x00
USB_TYPE_CLASS = 0x20
USB_RECIP_DEVICE = 0x00
USB_RECIP_INTERFACE = 0x01

# DFU class request type
DFU_REQUEST_OUT = USB_DIR_OUT | USB_TYPE_CLASS | USB_RECIP_INTERFACE  # 0x21
DFU_REQUEST_IN = USB_DIR_IN | USB_TYPE_CLASS | USB_RECIP_INTERFACE   # 0xA1

# Standard request type
STD_REQUEST_OUT = USB_DIR_OUT | USB_TYPE_STANDARD | USB_RECIP_DEVICE  # 0x00
STD_REQUEST_IN = USB_DIR_IN | USB_TYPE_STANDARD | USB_RECIP_DEVICE    # 0x80

# USB timeouts (ms)
USB_TIMEOUT_DEFAULT = 5000
USB_TIMEOUT_SHORT = 100
USB_TIMEOUT_ABORT = 10
USB_TIMEOUT_RESET = 1000

# Exploit constants
DFU_MAX_TRANSFER_SIZE = 0x800
PAYLOAD_OFFSET_ARMV7 = 0x400
PAYLOAD_OFFSET_ARM64 = 0x800

# Apple-inspired liquid glass colors
COLOR_BG = "#08081a"
COLOR_GLASS = "#16163a"
COLOR_GLASS_LIGHT = "#1c1c48"
COLOR_GLASS_BORDER = "#5858a8"
COLOR_GLASS_GLOW = "#7070c0"
COLOR_ACCENT = "#8b5cf6"
COLOR_ACCENT_HOVER = "#a78bfa"
COLOR_ACCENT_DIM = "#6d28d9"
COLOR_SUCCESS = "#34d399"
COLOR_WARNING = "#fbbf24"
COLOR_ERROR = "#f87171"
COLOR_INFO = "#94a3b8"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_DIM = "#7080a8"
COLOR_TEXT_BRIGHT = "#f8fafc"

# Fluid background blob colors (R, G, B) - muted, Apple-like
BLOB_COLORS = [
    (70, 30, 160),    # deep blue-purple
    (35, 75, 195),    # ocean blue
    (175, 45, 110),   # rose
    (20, 130, 130),   # teal
    (105, 50, 185),   # violet
    (170, 90, 35),    # warm amber
]

# Glass panel styling
GLASS_RADIUS = 22
GLASS_BORDER_WIDTH = 1

# Setup wizard window
WIZARD_WIDTH = 900
WIZARD_HEIGHT = 700
