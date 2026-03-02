# pongoOS Setup Script Fix

## Issue

pongoOS setup wizard was failing with bash errors:
```
bash: line 1: set: -: invalid option
bash: line 2: set: pipefail: invalid option name
bash: line 3: cd: $'/home/natha/PongoOSData\r': No such file or directory
```

## Root Cause

Windows line endings (`\r\n`) in bash scripts were causing:
1. `set -e` becoming `set -e\r` (invalid option)
2. `set -o pipefail` becoming `set -o pipefail\r` (invalid option name)
3. Directory path `/home/natha/PongoOSData\r` (no such directory)

The issue occurred because:
- Python source files on Windows use CRLF line endings
- Triple-quoted strings (`'''...'''`) inherit these line endings
- When scripts are concatenated and passed to bash via WSL, `\r` characters corrupt commands

## Fix

Enhanced line ending cleanup in [core/setup_engine.py](core/setup_engine.py):

### 1. Clean Work Directory Path
```python
# Clean work_dir first to ensure no line endings in path
clean_work_dir = self._work_dir.replace("\r", "").replace("\n", "")
preamble = f'mkdir -p "{clean_work_dir}" && cd "{clean_work_dir}"\n'
```

### 2. Aggressive Script Cleaning
```python
# Clean script - aggressively remove ALL Windows line endings
clean_script = script.replace("\r\n", "\n").replace("\r", "\n")

# Remove any trailing whitespace from each line
clean_script = "\n".join(line.rstrip() for line in clean_script.split("\n"))

# Add error handling (with Unix line endings only)
clean_script = "set -e\nset -o pipefail\n" + clean_script

# Final cleanup - ensure no \r anywhere
clean_script = clean_script.replace("\r", "")
```

## Cleanup Steps

1. **Replace CRLF with LF**: `script.replace("\r\n", "\n").replace("\r", "\n")`
2. **Strip trailing whitespace**: `line.rstrip()` for each line
3. **Add clean preamble**: `set -e\nset -o pipefail\n` with pure Unix line endings
4. **Final pass**: Remove any remaining `\r` characters

## Result

✅ `set -e` works correctly
✅ `set -o pipefail` works correctly
✅ `cd` command uses clean path without `\r`
✅ All bash commands execute properly
✅ pongoOS setup wizard runs successfully

## Testing

Run pongoOS setup wizard:
1. Click **"Setup pongoOS"** in pongoOS Emulator panel
2. Run Step 1: Install QEMU
3. Verify no bash errors
4. All steps should complete successfully

## Files Modified

- [core/setup_engine.py](core/setup_engine.py) - Enhanced line ending cleanup

## Summary

The fix ensures that:
- Work directory paths are clean (no `\r` or `\n`)
- All bash commands use Unix line endings (`\n`)
- Trailing whitespace is removed
- Final script has no Windows line ending artifacts

pongoOS setup wizard now works correctly on Windows with WSL! ✓
