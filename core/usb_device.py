"""
USB device manager for Apple DFU-mode devices.

Handles discovery, acquisition, and low-level USB communication
with iOS devices in DFU (Device Firmware Upgrade) mode.
"""

import re
import time
import usb.core
import usb.util
import usb.backend.libusb1 as libusb1

from config.constants import (
    APPLE_VID,
    DFU_PID,
    DFU_REQUEST_OUT,
    DFU_REQUEST_IN,
    DFU_DNLOAD,
    DFU_UPLOAD,
    DFU_GET_STATUS,
    DFU_CLR_STATUS,
    DFU_GET_STATE,
    DFU_ABORT,
    USB_TIMEOUT_DEFAULT,
    USB_TIMEOUT_SHORT,
    DFU_MAX_TRANSFER_SIZE,
)


class DeviceInfo:
    """Parsed device information from DFU serial string."""

    def __init__(self):
        self.cpid = 0
        self.cprv = 0
        self.bdid = 0
        self.ecid = 0
        self.ibfl = 0
        self.srtg = ""
        self.serial_string = ""

    def __repr__(self):
        return (
            f"DeviceInfo(cpid=0x{self.cpid:04X}, bdid=0x{self.bdid:02X}, "
            f"ecid=0x{self.ecid:016X}, srtg='{self.srtg}')"
        )


def parse_serial_string(serial):
    """
    Parse the DFU mode serial string into a DeviceInfo.

    Apple DFU serial strings look like:
    CPID:8015 CPRV:11 CPFM:03 SCEP:01 BDID:0E ECID:001A2B3C4D5E6F70 IBFL:3C SRTG:[iBoot-...]
    """
    info = DeviceInfo()
    info.serial_string = serial or ""

    if not serial:
        return info

    patterns = {
        "cpid": (r"CPID:([0-9A-Fa-f]+)", 16),
        "cprv": (r"CPRV:([0-9A-Fa-f]+)", 16),
        "bdid": (r"BDID:([0-9A-Fa-f]+)", 16),
        "ecid": (r"ECID:([0-9A-Fa-f]+)", 16),
        "ibfl": (r"IBFL:([0-9A-Fa-f]+)", 16),
    }

    for attr, (pattern, base) in patterns.items():
        match = re.search(pattern, serial)
        if match:
            setattr(info, attr, int(match.group(1), base))

    srtg_match = re.search(r"SRTG:\[([^\]]+)\]", serial)
    if srtg_match:
        info.srtg = srtg_match.group(1)

    return info


class DFUDevice:
    """
    Interface to an Apple device in DFU mode via pyusb.

    Provides methods for standard DFU operations (send data, get status,
    reset) as well as raw control transfers needed by the exploit.
    """

    def __init__(self, dev=None, timeout=USB_TIMEOUT_DEFAULT):
        self._dev = dev
        self.timeout = timeout
        self.info = DeviceInfo()

    @staticmethod
    def find(timeout=5.0):
        """
        Find an Apple device in DFU mode.

        Searches USB bus for Apple VID + DFU PID. Retries until
        timeout expires. Returns DFUDevice or None.
        """
        backend = libusb1.get_backend()
        deadline = time.time() + timeout

        while time.time() < deadline:
            dev = usb.core.find(
                idVendor=APPLE_VID,
                idProduct=DFU_PID,
                backend=backend,
            )
            if dev is not None:
                dfu = DFUDevice(dev)
                dfu._acquire()
                return dfu
            time.sleep(0.1)

        return None

    def _acquire(self):
        """Claim the USB device and parse its serial string."""
        try:
            self._dev.set_configuration()
        except usb.core.USBError:
            pass

        try:
            usb.util.claim_interface(self._dev, 0)
        except usb.core.USBError:
            pass

        serial = self._read_serial()
        self.info = parse_serial_string(serial)

    def _read_serial(self):
        """Read the device serial number string descriptor."""
        try:
            return usb.util.get_string(self._dev, self._dev.iSerialNumber)
        except (usb.core.USBError, ValueError):
            return ""

    def release(self):
        """Release the USB device."""
        if self._dev is None:
            return
        try:
            usb.util.release_interface(self._dev, 0)
        except usb.core.USBError:
            pass
        try:
            usb.util.dispose_resources(self._dev)
        except usb.core.USBError:
            pass
        self._dev = None

    # ---- DFU standard operations ----

    def dfu_send_data(self, data):
        """Send data to device via DFU_DNLOAD (wValue=0)."""
        self.ctrl_transfer(DFU_REQUEST_OUT, DFU_DNLOAD, 0, 0, data)

    def dfu_upload(self, length):
        """Read data from device via DFU_UPLOAD."""
        return self.ctrl_transfer(DFU_REQUEST_IN, DFU_UPLOAD, 0, 0, length)

    def dfu_get_status(self):
        """Get DFU status (6-byte response)."""
        return self.ctrl_transfer(DFU_REQUEST_IN, DFU_GET_STATUS, 0, 0, 6)

    def dfu_get_state(self):
        """Get DFU state (1-byte response)."""
        data = self.ctrl_transfer(DFU_REQUEST_IN, DFU_GET_STATE, 0, 0, 1)
        return data[0] if data else -1

    def dfu_clear_status(self):
        """Clear DFU error status."""
        self.ctrl_transfer(DFU_REQUEST_OUT, DFU_CLR_STATUS, 0, 0, None)

    def dfu_abort(self):
        """Abort current DFU operation."""
        self.ctrl_transfer(DFU_REQUEST_OUT, DFU_ABORT, 0, 0, None)

    # ---- Raw USB operations ----

    def ctrl_transfer(self, bm_request_type, b_request, w_value, w_index, data_or_length, timeout=None):
        """
        Perform a USB control transfer.

        For OUT transfers, data_or_length is bytes to send.
        For IN transfers, data_or_length is number of bytes to read.
        """
        if timeout is None:
            timeout = self.timeout
        try:
            return self._dev.ctrl_transfer(
                bm_request_type, b_request, w_value, w_index,
                data_or_length, timeout=timeout,
            )
        except usb.core.USBTimeoutError:
            return None
        except usb.core.USBError as e:
            if e.errno == 5:  # IO error - often expected during exploit
                return None
            raise

    def ctrl_transfer_no_error(self, bm_request_type, b_request, w_value, w_index, data_or_length, timeout=None):
        """Control transfer that swallows all USB errors."""
        try:
            return self.ctrl_transfer(
                bm_request_type, b_request, w_value, w_index,
                data_or_length, timeout=timeout,
            )
        except usb.core.USBError:
            return None

    def usb_reset(self):
        """Perform a USB bus reset on the device."""
        try:
            self._dev.reset()
        except usb.core.USBError:
            pass

    def reconnect(self, timeout=5.0):
        """Release current handle and find the device again."""
        self.release()
        time.sleep(0.5)
        new_dev = DFUDevice.find(timeout=timeout)
        if new_dev:
            self._dev = new_dev._dev
            self.info = new_dev.info
            return True
        return False

    @property
    def connected(self):
        """Check if device handle is still valid."""
        if self._dev is None:
            return False
        try:
            self._dev.ctrl_transfer(DFU_REQUEST_IN, DFU_GET_STATE, 0, 0, 1, timeout=USB_TIMEOUT_SHORT)
            return True
        except usb.core.USBError:
            return False

    @property
    def usb_device(self):
        """Access the underlying pyusb device object."""
        return self._dev
