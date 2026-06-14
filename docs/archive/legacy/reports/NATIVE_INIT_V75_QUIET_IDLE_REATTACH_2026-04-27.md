# Native Init v75 Quiet Idle Reattach Report (2026-04-27)

## Summary

- Version: `A90 Linux init 0.8.6 (v75)`
- Source: `stage3/linux_init/init_v75.c`
- Boot image: `stage3/boot_linux_v75.img`
- Goal: keep serial idle recovery active, but stop successful idle reattach cycles from flooding the on-screen `LOG TAIL`.

## Change

- Increased `CONSOLE_IDLE_REATTACH_MS` from `10000` to `60000`.
- Suppressed native log/klog request+ok lines only for `reason=idle-timeout`.
- Kept wait/open failure logs for idle reattach.
- Kept manual/non-idle reattach logs such as `reason=command`, `usbacmreset`, `poll-fault`, `read-error`, and USB rebind paths.
- Added on-device changelog entry: `0.8.6 v75 QUIET IDLE REATTACH`.

## Artifacts

- `stage3/linux_init/init_v75`
  - SHA256 `840d1cd349b203dd912e3c99dd6b799acfc4fe2f0295c52bdf3f0e9cfe4df1fe`
- `stage3/ramdisk_v75.cpio`
  - SHA256 `af5abb98fdd3f49a767a75db8bda51bcbfea1a9ed75b9e1f6c4dd781c28eb072`
- `stage3/boot_linux_v75.img`
  - SHA256 `50f76a3a9e84ad13f19116e9b6e5b3a1ece6a91b177b81ae8cab1509109452a5`

## Validation

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o stage3/linux_init/init_v75 stage3/linux_init/init_v75.c` — PASS
- `aarch64-linux-gnu-strip stage3/linux_init/init_v75` — PASS
- boot image repack from v74 kernel/boot args with v75 ramdisk — PASS
- marker strings in `stage3/boot_linux_v75.img`:
  - `A90 Linux init 0.8.6 (v75)`
  - `A90v75`
  - `0.8.6 v75 QUIET IDLE REATTACH`
- flash path:
  - native init v74 → TWRP recovery → boot partition flash → v75 system boot — PASS
  - `native_init_flash.py ... --verify-protocol auto` verified `cmdv1 version/status` with `rc=0`, `status=ok`.
- idle log behavior:
  - after 70+ seconds idle, `/cache/native-init.log` did not gain new `idle-timeout` request/ok success lines — PASS
  - manual `a90ctl.py --json reattach` still logs `reason=command` request/ok lines — PASS

## Current Baseline

`0.8.6 (v75)` is now the latest verified native init baseline.

The v48 fallback image remains the known-good rescue path, and v49 remains an isolated failed experiment.
