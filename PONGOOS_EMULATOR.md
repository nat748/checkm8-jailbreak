# pongoOS QEMU Emulator

A QEMU-based emulator running pongoOS for testing the checkm8 exploit without physical hardware.

## What is pongoOS?

pongoOS is a pre-boot execution environment developed by the checkra1n team. It runs after the checkm8 bootrom exploit and provides:
- Kernel patching capabilities
- Secure boot bypass
- Custom boot arguments
- Memory inspection and modification
- Interactive console for debugging

This is what runs on your device after checkm8 exploitation, before booting iOS.

## Features

### pongoOS-QEMU Integration
- **QEMU ARM64 emulator** running pongoOS
- **Virtual DFU device** for exploit testing
- **Serial console** with interactive commands
- **No physical hardware required**

### GUI Panel
- **Launch/Stop** emulator with one click
- **Setup Wizard** for automatic installation
- **Console Window** to interact with pongoOS
- **Real-time output** from pongoOS serial console

## Setup

### Option 1: Automated Setup (Recommended)

1. Click **"Setup pongoOS"** button in the pongoOS Emulator panel
2. Follow the 3-step automated wizard:
   - **Step 1**: Install QEMU emulator
   - **Step 2**: Download and build pongoOS-QEMU
   - **Step 3**: Test the emulator

Total time: ~5-10 minutes

### Option 2: Manual Setup

#### Prerequisites

**macOS:**
```bash
brew install qemu
```

**Linux:**
```bash
sudo apt-get install qemu-system-aarch64
```

**Windows:**
- Install WSL 2 with Ubuntu
- Run inside WSL:
```bash
sudo apt-get install qemu-system-aarch64
```

#### Build pongoOS-QEMU

```bash
# Clone the QEMU-optimized fork
git clone https://github.com/citruz/pongoOS-QEMU.git
cd pongoOS-QEMU

# Build
make

# Copy binary to checkm8 data directory
mkdir -p ~/PongoOSData
cp build/pongoOS ~/PongoOSData/
```

## Usage

### 1. Launch Emulator

Click **"Launch Emulator"** in the pongoOS Emulator panel.

QEMU will start and boot pongoOS. You should see:
```
Booting pongoOS...
pongoOS version 2.x.x
Serial console ready
>
```

### 2. Open Console

Click **"Console"** to open the pongoOS console window.

This shows real-time output from pongoOS and allows you to send commands.

### 3. Test Exploit

1. Launch pongoOS emulator
2. Click **"Detect Device"** in the Device panel
3. The emulator will be detected as a virtual DFU device
4. Click **"Run Exploit"**
5. Watch the exploit run against the virtual device

### 4. Interactive Console

In the console window, you can send pongoOS commands:

**Common commands:**
- `help` - Show available commands
- `version` - Show pongoOS version
- `bootx` - Boot iOS kernel (if loaded)
- `xargs <args>` - Set boot arguments
- `memcpy <src> <dst> <len>` - Copy memory
- `hexdump <addr> <len>` - Dump memory as hex

**Example session:**
```
> version
pongoOS version 2.7.0
Build: Dec 15 2023 10:30:00

> help
Available commands:
  help      - Show this message
  version   - Show version info
  bootx     - Boot loaded kernel
  xargs     - Set boot arguments
  ...

> xargs -v debug=0x2014e
Boot args set: -v debug=0x2014e
```

## Architecture

### Components

```
┌──────────────────────────────────────┐
│         checkm8 GUI                  │
│  ┌────────────────────────────────┐  │
│  │     PongoOSPanel (UI)          │  │
│  └────────────────────────────────┘  │
│              ↓                        │
│  ┌────────────────────────────────┐  │
│  │  PongoOSEmulator (Core)        │  │
│  │   - QEMU process management    │  │
│  │   - Serial console I/O         │  │
│  │   - USB DFU emulation          │  │
│  └────────────────────────────────┘  │
│              ↓                        │
│  ┌────────────────────────────────┐  │
│  │      QEMU ARM64                │  │
│  │   - virt machine type          │  │
│  │   - Cortex-A57 CPU             │  │
│  │   - 512MB RAM                  │  │
│  │   - Serial console             │  │
│  │   - USB controller             │  │
│  └────────────────────────────────┘  │
│              ↓                        │
│  ┌────────────────────────────────┐  │
│  │        pongoOS                 │  │
│  │   - Bootloader/PXE             │  │
│  │   - Console commands           │  │
│  │   - Memory access              │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### QEMU Configuration

**Machine**: `virt` (ARM Virtual Machine)
- Generic ARM64 virtual board
- Flexible I/O configuration
- Good QEMU support

**CPU**: `cortex-a57`
- ARM Cortex-A57 (ARMv8-A)
- 64-bit architecture
- Compatible with pongoOS

**Memory**: 512MB RAM
- Sufficient for pongoOS
- Matches typical iOS device memory layout

**Serial Console**: `mon:stdio`
- Serial output to stdout
- QEMU monitor commands available (Ctrl+A X to quit)

**USB Controller**: `usb-serial`
- Virtual USB device
- Socket-based communication (port 1337)
- Allows DFU mode emulation

### pongoOS-QEMU Fork

The [citruz/pongoOS-QEMU](https://github.com/citruz/pongoOS-QEMU) fork includes:
- QEMU-specific patches
- Virtual hardware support
- USB emulation improvements
- Easier build process

This is preferred over the standard checkra1n/pongoOS for emulation.

## Files

| File | Purpose |
|------|---------|
| `core/pongoos_emulator.py` | QEMU process management |
| `gui/pongoos_panel.py` | UI control panel |
| `gui/pongoos_console.py` | Console window |
| `config/pongoos_setup.py` | Setup wizard steps |
| `~/PongoOSData/pongoOS` | Compiled pongoOS binary |

## Differences from Inferno

| Feature | pongoOS | Inferno |
|---------|---------|---------|
| **Purpose** | Bootloader/PXE | Full iOS emulator |
| **Complexity** | Simple | Complex |
| **Boot** | Boots in seconds | Takes minutes |
| **iOS** | No iOS | Full iOS 14 |
| **Size** | ~1MB binary | ~30GB setup |
| **Use Case** | Exploit testing | Full jailbreak testing |

**When to use pongoOS:**
- Quick checkm8 exploit testing
- Development/debugging
- Learning about boot process
- No need for full iOS

**When to use Inferno:**
- Full jailbreak testing
- App installation (Sileo)
- iOS feature testing
- Complete device emulation

## Troubleshooting

### "pongoOS binary not found"
- Run the Setup Wizard
- Or manually build pongoOS-QEMU
- Ensure binary is at `~/PongoOSData/pongoOS`

### "QEMU not found"
**macOS:**
```bash
brew install qemu
```

**Linux/WSL:**
```bash
sudo apt-get install qemu-system-aarch64
```

### Emulator starts but no output
- Check console window
- Serial output may be delayed
- Press Enter to get prompt

### "Permission denied" on launch
Make sure pongoOS binary is executable:
```bash
chmod +x ~/PongoOSData/pongoOS
```

### Build fails
**Missing dependencies:**
```bash
# macOS
xcode-select --install

# Linux
sudo apt-get install build-essential clang lld
```

## Advanced Usage

### Custom QEMU Arguments

Edit `core/pongoos_emulator.py`, `_build_qemu_command()`:

```python
cmd = [
    qemu_exec,
    "-M", "virt",
    "-cpu", "cortex-a57",
    "-m", "1G",  # Increase RAM
    "-kernel", str(pongo_bin),
    "-nographic",
    "-serial", "mon:stdio",
    "-gdb", "tcp::1234",  # Enable GDB debugging
]
```

### Connect GDB

```bash
# In terminal 1: Launch emulator
python main.py

# In terminal 2: Connect GDB
gdb-multiarch
(gdb) target remote localhost:1234
(gdb) continue
```

### USB DFU Testing

The emulator creates a virtual USB socket on port 1337:

```bash
# Connect to virtual USB
nc localhost 1337
```

This allows testing DFU protocol communication.

## Resources

- [pongoOS GitHub](https://github.com/checkra1n/pongoOS)
- [pongoOS-QEMU Fork](https://github.com/citruz/pongoOS-QEMU)
- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [checkra1n](https://checkra.in/)

## Summary

The pongoOS emulator provides a fast, lightweight way to test checkm8 exploitation without physical devices. It's perfect for development, debugging, and learning about the iOS boot process.

**Key benefits:**
- ✅ No hardware needed
- ✅ Fast boot (seconds)
- ✅ Interactive console
- ✅ Exploit testing
- ✅ Easy setup

Launch it, test exploits, and explore pongoOS commands! 🚀
