# checkm8 GUI

A modern graphical interface for the checkm8 bootrom exploit (CVE-2019-8900) targeting Apple A5–A11 chips, with integrated Inferno iPhone 11 emulator support.

<p align="center">
  <img src="assets/icon.png" alt="checkm8 logo" width="128">
</p>

## Features

- **Liquid Glass UI** — Modern Apple-inspired interface with animated gradient background
- **USB DFU Detection** — Automatic detection of devices in DFU mode
- **checkm8 Exploit** — Full exploitation pipeline for A5-A11 chips (iPhone 4S through iPhone X)
- **Inferno Emulator** — Full iPhone 11 (iOS 14) emulation via QEMU
- **pongoOS Emulator** — Fast QEMU ARM64 virtual device running pongoOS bootloader for exploit testing
- **Setup Wizards** — Automated installation for both emulators (all platforms)
- **Bootstrap Installer** — One-click checkra1n bootstrap installation (Sileo package manager)
- **Auto-Updater** — Automatic update notifications from GitHub releases
- **Multi-Platform** — Windows (via WSL), macOS, Linux

## Quick Start

### Running from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run the GUI
python main.py
```

### Running Pre-Built Packages

**Windows:**
- Download `checkm8-1.0.0-setup.exe` from releases
- Run the installer or use the portable version in `checkm8/` folder

**macOS:**
- Download `checkm8.app` or `checkm8-1.0.0.pkg` from releases
- Drag to Applications or run the installer

**Linux (Debian/Ubuntu):**
```bash
sudo dpkg -i checkm8_1.0.0_amd64.deb
checkm8
```

## Building Distributables

See [BUILD.md](BUILD.md) for detailed instructions on creating `.exe`, `.app`, `.pkg`, and `.deb` packages.

```bash
# Quick build for current platform
python build.py
```

## Supported Devices

| Chip | Devices | Support |
|------|---------|---------|
| A5 | iPhone 4S | ✓ |
| A6 | iPhone 5, 5C | ✓ |
| A7 | iPhone 5S, iPad Air | ✓ |
| A8 | iPhone 6, 6 Plus | ✓ |
| A9 | iPhone 6S, 6S Plus, SE (1st gen) | ✓ |
| A10 | iPhone 7, 7 Plus | ✓ |
| A11 | iPhone 8, 8 Plus, X | ✓ |
| A13 | iPhone 11 (Inferno emulator) | ✓ Emulated |

## Usage

### 1. Physical Device Jailbreak

1. Put your device in **DFU mode** (see DFU card in app)
2. Connect via USB
3. Click **"Detect Device"**
4. Click **"Run Exploit"**
5. Wait for "Device pwned" confirmation

### 2. Inferno Emulator Setup

1. Click **"Setup Wizard"** in the Emulator panel
2. Follow the automated setup steps:
   - Install dependencies
   - Clone & build Inferno
   - Download iOS firmware
   - Generate tickets
3. Launch the emulator with **"Launch Emulator"**
4. Click **"Detect Device"** to find the emulated iPhone
5. Run the exploit (simulated)
6. After emulator is stopped, click **"Install Sileo"** to add the jailbreak bootstrap

### 3. Manual Inferno Setup

If you prefer manual setup or encounter issues with the wizard, follow the official Inferno guide:
- https://chefkiss.dev/guides/inferno/

The wizard automates most of these steps but some (SEP firmware extraction, iOS restore) require manual intervention.

## Requirements

### For Running (Source)
- Python 3.8+
- CustomTkinter 5.2+
- PyUSB 1.2+
- libusb 1.0+
- Pillow 10.0+

### For Inferno Emulator
- **Windows:** WSL 2 with Ubuntu
- **macOS:** Xcode Command Line Tools
- **Linux:** Standard build tools (gcc, make, etc.)
- At least 6 GB RAM
- 32 GB free disk space
- Moderately fast CPU (emulation is intensive)

### For Building Packages
- PyInstaller 5.13+
- Platform-specific tools (see [BUILD.md](BUILD.md))

## Project Structure

```
checkm8-jailbreak/
├── main.py                 # Entry point
├── config/                 # Configuration & constants
│   ├── constants.py        # UI colors, USB IDs
│   ├── device_configs.py   # Per-chip exploit parameters
│   ├── emulator_config.py  # QEMU launch commands
│   └── setup_steps.py      # Wizard step definitions
├── core/                   # Exploit logic
│   ├── exploit_engine.py   # Main exploit orchestration
│   ├── emulator_exploit.py # Simulated exploit for Inferno
│   ├── usb_device.py       # DFU USB communication
│   ├── checkm8.py          # Low-level exploit primitives
│   ├── bootstrap.py        # Sileo bootstrap installer
│   └── setup_engine.py     # Setup wizard execution
├── gui/                    # User interface
│   ├── app.py              # Main window
│   ├── device_panel.py     # Device info panel
│   ├── exploit_panel.py    # Exploit controls
│   ├── emulator_panel.py   # Emulator controls
│   ├── log_panel.py        # Console output
│   ├── setup_window.py     # Setup wizard dialog
│   ├── about_window.py     # Credits & licenses
│   └── fluid_background.py # Animated gradient
└── payloads/               # Shellcode
    └── shellcode.py        # ARMv7 & ARM64 payloads
```

## Credits & Licenses

This project integrates multiple open-source tools and exploits. Full credits are available in the **About** window of the application or in [gui/about_window.py](gui/about_window.py).

Key contributors:
- **axi0mX** — checkm8 exploit (CVE-2019-8900)
- **ChefKissInc** — Inferno iPhone 11 emulator
- **checkra1n team** — Jailbreak bootstrap & Sileo loader
- **libimobiledevice project** — iOS device communication
- **Tom Schimansky** — CustomTkinter UI framework

See the About window for complete list with links.

## Legal Notice

This tool is provided for **educational and authorized security research purposes only**.

- Do not use this tool for unauthorized access to devices you don't own
- The checkm8 exploit is a **hardware vulnerability** and cannot be patched via software updates
- Always comply with local laws regarding device modifications
- iOS firmware files (IPSW) are copyrighted by Apple Inc. and subject to their EULA
- Do NOT distribute encryption keys, firmware files, or circumvent DRM

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run from source
python main.py

# Run tests (if any)
python -m pytest

# Build packages
python build.py

# Clean build artifacts
python build.py --clean
```

## Contributing

This is a research and educational project. Contributions, bug reports, and feature requests are welcome via GitHub issues and pull requests.

## Support

- Check [CLAUDE.md](CLAUDE.md) for project architecture and conventions
- See [BUILD.md](BUILD.md) for packaging instructions
- Refer to the [Inferno documentation](https://chefkiss.dev/guides/inferno/) for emulator setup
- Open an issue for bugs or feature requests

## License

This project includes code from multiple open-source projects, each with their own licenses:
- checkm8 exploit — See original repository licenses
- Inferno emulator — QEMU GPL 2.0
- CustomTkinter — MIT License
- PyUSB — BSD License

Check individual component licenses for details. This GUI wrapper is provided as-is for educational purposes.
