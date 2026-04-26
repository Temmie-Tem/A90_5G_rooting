# Native Init v72 Display Test Report (2026-04-27)

## Summary

- Version: `A90 Linux init 0.8.3 (v72)`
- Source: `stage3/linux_init/init_v72.c`
- Goal: add an on-device display diagnostic screen and correct framebuffer color output.
- Status: built, flashed, and verified through the serial bridge.

## What Changed

- Added `TOOLS / DISPLAY TEST` to the on-device tools menu.
- Added `displaytest` shell command for direct framebuffer testing.
- Added a color palette, font scale ladder, wrap sample, and safe-area grid.
- Split the top guide into `TOP LEFT SLOT`, `PUNCH HOLE`, and `TOP RIGHT SLOT`.
- Widened the main safe-area grid so usable portrait space is easier to judge.
- Fixed framebuffer color packing for `DRM_FORMAT_XBGR8888`, correcting swapped red/blue and yellow/cyan output.
- Added on-device changelog entry for `0.8.3 v72`.

## Build Artifacts

- `stage3/linux_init/init_v72`
  - SHA256 `3215710e0e5cc4038dea74b0f22575cbeda9e90625cb53b45f702db2b4f08619`
- `stage3/ramdisk_v72.cpio`
  - SHA256 `7e8cad648cec15d7dffe1cb9e8a2b2afa1aa297a01b9450234c26b1cd6ffcc41`
- `stage3/boot_linux_v72.img`
  - SHA256 `2f7e7927f1f22d540a37d7bafd7176730bae24bee418dfb667bfd6805cf0eebf`

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v72.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.3 (v72)" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Result:

- local marker check: PASS
- local image SHA256: `2f7e7927f1f22d540a37d7bafd7176730bae24bee418dfb667bfd6805cf0eebf`
- TWRP ADB push: PASS
- remote `/tmp/native_init_boot.img` SHA256: PASS
- boot partition prefix SHA256: PASS
- reboot to native init: PASS
- bridge `version`: `A90 Linux init 0.8.3 (v72)` PASS

## Runtime Validation

Bridge check:

```bash
printf 'displaytest\nstatus\nautohud 2\nstatus\n' | nc -w 10 127.0.0.1 54321
```

Observed:

- `displaytest` → framebuffer presented at `1080x2400`
- `status` after `displaytest` → `autohud: stopped`, expected for `CMD_DISPLAY`
- `autohud 2` → auto HUD restarted
- final `status` → `autohud: running`

## Visual Check

- The display test now marks the punch-hole danger zone separately from top-left/top-right slots.
- RED/BLUE/YELLOW/CYAN should match their labels after the `XBGR8888` packing fix.
