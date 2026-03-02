# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

checkm8 is a Windows GUI tool implementing the checkm8 bootrom exploit (CVE-2019-8900) for Apple A5–A11 chips (iPhone 4S through iPhone X). It uses a use-after-free vulnerability in the DFU USB stack to gain bootrom-level code execution and disable signature verification.

## Commands

```bash
pip install -r requirements.txt   # Install dependencies
python main.py                    # Launch the GUI application
```

There are no tests, linting, or build steps configured. The app requires a physical iOS device in DFU mode and a working libusb backend for USB access.

## Architecture

The app follows a three-layer architecture: **GUI → Engine → USB primitives**.

### Exploit flow (core/)

`ExploitEngine` (exploit_engine.py) orchestrates the full exploit as a 10-stage pipeline running in a background thread:

1. **Detect** — `DFUDevice.find()` searches USB bus for Apple VID `0x05AC` + DFU PID `0x1227`
2. **Identify** — Parses CPID from the DFU serial string descriptor, looks up chip config
3. **Heap feng shui** — Controlled alloc/free sequences to arrange heap predictably (chip-specific parameters from `device_configs.py`)
4. **Stall** — `DFU_DNLOAD` with no data body to stall EP0
5. **Trigger UAF** — Partial `DFU_DNLOAD` + USB reset frees the IO buffer while DFU state still references it
6. **Overwrite** — Heap spray reclaims freed region with crafted function pointers (ARMv7: repeated callback ptr, ARM64: func ptr + trampoline at offset 0x100)
7. **Payload** — Sends architecture-specific shellcode that patches signature verification
8. **Verify** — Checks if device accepts a DFU upload (pwned devices respond differently)

`checkm8.py` contains the low-level exploit primitives (stateless functions operating on a `DFUDevice`). `usb_device.py` wraps pyusb for DFU-specific control transfers. The `ctrl_transfer_no_error` variant swallows USB errors, which is intentional—many exploit steps expect errors.

### GUI (gui/)

Built with CustomTkinter. `App` (app.py) is the main window using `place()` with relative coordinates for auto-scaling layout. Worker threads communicate with the GUI via `queue.Queue` polled at 16ms intervals (~60fps).

- **FluidBackground** — PIL-based animated gradient blobs rendered at 25% resolution, bilinear-upscaled for smooth blur effect. Runs at 20fps.
- **DevicePanel / ExploitPanel / LogPanel** — Self-contained glass panels with public state-change methods (e.g. `set_detecting()`, `set_running()`, `update_progress()`).

All background work (device detection, exploit execution) runs in daemon threads. GUI updates from threads must go through the queue system (`_log_t`, `_progress_t`) to maintain thread safety—never call tkinter widgets directly from worker threads.

### Config (config/)

- `constants.py` — USB protocol constants, DFU request codes, UI colors, and glass panel styling
- `device_configs.py` — Per-chip exploit parameters keyed by CPID (hex). Each config has arch, heap feng shui counts (`large_leak`, `hole`, `leak`), memory addresses, and max payload size. ARM64 configs also have `func_ptr` and `block_size`.

### Payloads (payloads/)

`shellcode.py` contains raw ARMv7 (Thumb-2) and ARM64 (AArch64) instruction bytes. Payloads are padded to `max_size` from device config with a `CHECKM8\0` magic marker at offset `0x100` for verification.

## Key Conventions

- All USB constants and color values are centralized in `config/constants.py`—don't hardcode hex values elsewhere.
- Device configs use CPID (Chip Product ID) as the lookup key. A11 (`0x8015`) is the only chip needing `large_leak > 0`.
- The overwrite buffer is always `0x800` bytes. ARMv7 fills with 4-byte repeated addresses; ARM64 fills with 8-byte pointers and places a trampoline at offset `0x100`.
- Payload data is sent in `DFU_MAX_TRANSFER_SIZE` (`0x800`) chunks.
- Windows 11 DWM effects (rounded corners, acrylic backdrop) are applied via ctypes in `app.py` and are fail-safe.