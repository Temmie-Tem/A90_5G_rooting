# Native Init v78 SD Workspace Report (2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.9 (v78)`
- Source: `stage3/linux_init/init_v78.c`
- Boot image: `stage3/boot_linux_v78.img`
- Goal: promote ext4 SD storage into a first-class, safer experiment workspace while keeping internal UFS focused on boot/rescue state.

## Change

- Promoted the SD workspace from the v77 working tree into its own feature version.
- Added `mountsd [status|ro|rw|off|init]`.
- Standardized `/mnt/sdext/a90` as the native init workspace.
- Created workspace subdirectories:
  - `bin`
  - `logs`
  - `tmp`
  - `rootfs`
  - `images`
  - `backups`
- Added `mountsd` state, mount line, and size/free-space reporting.
- Integrated `mountsd status` into the general `status` command.
- Added on-device changelog entry: `0.8.9 v78 SD WORKSPACE`.

## Artifacts

- `stage3/linux_init/init_v78`
  - SHA256 `fc2b8f57482deddfe31885e8089e2047d7af08c3ac36414a1e644a2d43ed7274`
- `stage3/ramdisk_v78.cpio`
  - SHA256 `d1e37f098b9a15e2b00e016b882ec40b3fd68ce81f3c68d0a7c303e7a7958fd8`
- `stage3/boot_linux_v78.img`
  - SHA256 `2f57f29e623838601b664001b92bb4ac43e47e03eb0d9cb45bd86322ec52d099`

## Validation

- Static ARM64 build — PASS
- v78 ramdisk and boot image generation — PASS
- boot image marker strings:
  - `A90 Linux init 0.8.9 (v78)`
  - `A90v78`
  - `0.8.9 v78 SD WORKSPACE`
- SD formatting validation:
  - `/dev/block/mmcblk0p1`
  - label `A90_NATIVE`
  - filesystem `ext4`
- `mountsd init` created `/mnt/sdext/a90/{bin,logs,tmp,rootfs,images,backups}`.
- Write/sync/read probe at `/mnt/sdext/a90/tmp/mountsd_probe.txt` — PASS
- `mountsd ro`, `mountsd off`, `mountsd status`, and final `status` integration — PASS

## Current Baseline

`0.8.9 (v78)` is now the latest verified native init baseline.

The v48 fallback image remains the known-good rescue path, and v49 remains an isolated failed experiment.
