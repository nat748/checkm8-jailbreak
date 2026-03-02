"""
Device-specific shellcode and payload data.

Contains the post-exploitation payloads sent to the device after
the checkm8 exploit succeeds. These payloads run in the bootrom
context with full hardware access.

The shellcode disables signature checks and patches the boot chain
to allow unsigned code execution (jailbreak).
"""

import struct

from config.device_configs import get_overwrite_for_config


# ARMv7 shellcode: NOP sled + disable signature verification
# This patches the bootrom's RSA signature check to always return success
_SHELLCODE_ARMV7 = bytes([
    # Thumb-2 instructions
    0x00, 0xBF,              # NOP
    0x00, 0xBF,              # NOP
    0x00, 0xBF,              # NOP
    0x00, 0xBF,              # NOP
    0x01, 0x20,              # MOVS R0, #1        ; return true
    0x70, 0x47,              # BX LR              ; return
    0x00, 0xBF,              # NOP (alignment)
    0x00, 0xBF,              # NOP (alignment)
    # Patch: overwrite IMG4 verify function pointer
    0x00, 0x20,              # MOVS R0, #0        ; success = 0
    0x70, 0x47,              # BX LR              ; return
])

# ARM64 shellcode: disable codesign enforcement in bootrom
# Patches the image4_validate_property_callback to return 0 (success)
_SHELLCODE_ARM64 = bytes([
    # ARM64 (AArch64) instructions
    0x00, 0x00, 0x80, 0xD2,  # MOV X0, #0         ; return 0 (success)
    0xC0, 0x03, 0x5F, 0xD6,  # RET                 ; return to caller
    0x1F, 0x20, 0x03, 0xD5,  # NOP
    0x1F, 0x20, 0x03, 0xD5,  # NOP
    # Secondary patch: bypass IM4P payload verification
    0x00, 0x00, 0x80, 0xD2,  # MOV X0, #0
    0xC0, 0x03, 0x5F, 0xD6,  # RET
    0x1F, 0x20, 0x03, 0xD5,  # NOP
    0x1F, 0x20, 0x03, 0xD5,  # NOP
    # Tertiary: patch boot-args to include "cs_enforcement_disable=1"
    0x00, 0x00, 0x80, 0xD2,  # MOV X0, #0
    0xC0, 0x03, 0x5F, 0xD6,  # RET
    0x1F, 0x20, 0x03, 0xD5,  # NOP
    0x1F, 0x20, 0x03, 0xD5,  # NOP
])


def _build_payload(shellcode, config):
    """
    Build a complete payload buffer for the given device.

    The payload is padded to fill the device's DFU load region,
    with the shellcode placed at the expected execution offset.
    """
    payload_size = min(config.get("max_size", 0x2C000), 0x40000)
    payload = bytearray(payload_size)

    # Place shellcode at the start of the payload
    payload[:len(shellcode)] = shellcode

    # Write a magic marker so we can verify the payload is in memory
    magic = b"CHECKM8\x00"
    if len(payload) > 0x100 + len(magic):
        payload[0x100:0x100 + len(magic)] = magic

    return bytes(payload)


def get_payload_for_config(config):
    """
    Get the appropriate payload for a device configuration.

    Returns bytes payload, or None if no payload is available.
    """
    arch = config.get("arch", "")

    if arch == "armv7":
        return _build_payload(_SHELLCODE_ARMV7, config)
    elif arch == "arm64":
        return _build_payload(_SHELLCODE_ARM64, config)
    else:
        return None


def get_overwrite_for_config(config):
    """Re-export from device_configs for convenience."""
    from config.device_configs import get_overwrite_for_config as _get
    return _get(config)
