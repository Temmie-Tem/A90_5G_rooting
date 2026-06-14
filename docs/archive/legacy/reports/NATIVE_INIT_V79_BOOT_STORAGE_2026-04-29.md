# Native Init v79 Boot Storage Report (2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.10 (v79)`
- Source: `stage3/linux_init/init_v79.c`
- Boot image: `stage3/boot_linux_v79.img`
- Goal: validate the known SD card during boot, promote it to main runtime storage only when healthy, and fall back to `/cache` with a visible warning when unsafe.

## Change

- Added boot-time SD health check before the main HUD starts.
- Checks `/dev/block/mmcblk0p1` and reads the ext4 UUID directly from the superblock.
- Expected SD UUID: `c6c81408-f453-11e7-b42a-23a2c89f58bc`
- Mounts the SD read/write at `/mnt/sdext`.
- Verifies or initializes `/mnt/sdext/a90/.a90-native-id`.
- Runs a write/sync/read probe at `/mnt/sdext/a90/tmp/.boot-rw-test`.
- Uses `/mnt/sdext/a90` as main runtime storage when all checks pass.
- Switches native log output to `/mnt/sdext/a90/logs/native-init.log` when SD is healthy.
- Falls back to `/cache` if SD is missing, changed, fails to mount, or fails the read/write probe.
- Shows SD probe progress on the boot splash.
- Shows persistent SD warning text on the HUD when fallback is active.
- Added `storage` command and storage lines inside `status`.
- Added UUID match reporting to `mountsd status`.
- Added on-device changelog entry: `0.8.10 v79 BOOT SD PROBE`.

## Artifacts

- `stage3/linux_init/init_v79`
  - SHA256 `c631667a18a55c91e829a24211b5425bdcad2c24c3d4ef7aef98a0745d9e4d03`
- `stage3/ramdisk_v79.cpio`
  - SHA256 `68cb4b6764c5d8a106a24f4b270e5e96bf5a266fa11926213a78640a02a50cf1`
- `stage3/boot_linux_v79.img`
  - SHA256 `1e7363085c3edb541b88b360c6e801eef6fcc67feb421b752bdc236c805b8318`

## Local Validation

- Static ARM64 build — PASS
- v79 ramdisk and boot image generation — PASS
- Boot image marker strings:
  - `A90 Linux init 0.8.10 (v79)`
  - `A90v79`
  - `0.8.10 v79 BOOT SD PROBE`
  - `c6c81408-f453-11e7-b42a-23a2c89f58bc`
  - `[ SD     ] UUID OK`
  - `[ STORAGE] SD MAIN READY`

## Device Validation

- Flash `stage3/boot_linux_v79.img` from TWRP recovery — PASS
- Post-boot `cmdv1 version` and `cmdv1 status` verification — PASS
- `storage` through the bridge — PASS
  - `backend=sd`
  - `root=/mnt/sdext/a90`
  - `fallback=no`
  - `expected=yes`
  - `rw=yes`
  - `uuid=c6c81408-f453-11e7-b42a-23a2c89f58bc`
- `mountsd status` through the bridge — PASS
  - `match=yes`
  - `state=mounted`
  - `mode=rw`
  - `size=59968MB`
  - `avail=56863MB`
- `status` storage section — PASS
  - `backend=sd`
  - `root=/mnt/sdext/a90`
  - `fallback=no`
  - `log=/mnt/sdext/a90/logs/native-init.log`

Fallback validation with missing/changed SD is intentionally deferred until a safe physical test window.

## Current Baseline

`0.8.10 (v79)` is the latest field-verified native init build.

The v48 fallback image remains the known-good rescue path, and v49 remains an isolated failed experiment.
