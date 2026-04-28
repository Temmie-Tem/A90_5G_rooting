# Native Init v77 Display Test + SD Workspace Report (2026-04-27~2026-04-29)

## Summary

- Version: `A90 Linux init 0.8.8 (v77)`
- Source: `stage3/linux_init/init_v77.c`
- Boot image: `stage3/boot_linux_v77.img`
- Goal: split the crowded display test into focused pages, add camera-hole calibration, and make ext4 SD the safe experiment workspace.

## Change

- Added `draw_screen_display_test_page(page)`.
- Kept `draw_screen_display_test()` as page 0 compatibility wrapper.
- Added four display test pages:
  - page 1: color palette and XBGR8888 pixel format check
  - page 2: font scale and wrap sample
  - page 3: safe/cutout calibration reference
  - page 4: HUD/menu layout preview
- Added `cutoutcal [x y size]`:
  - default reference is `x=540 y=80 size=49` on the 1080x2400 panel
  - explicit coordinates can be rendered from the bridge for visual iteration
- Added `TOOLS > CUTOUT CAL` interactive app:
  - VOL+/VOL- adjusts the selected field
  - POWER cycles `X`, `Y`, `SIZE`
  - POWER long/double or VOL+DN exits back to the menu
- Formatted SD partition `/dev/block/mmcblk0p1` as `ext4` label `A90_NATIVE`.
- Added `mountsd [status|ro|rw|off|init]`.
- Added standard workspace `/mnt/sdext/a90`:
  - `bin`
  - `logs`
  - `tmp`
  - `rootfs`
  - `images`
  - `backups`
- Added `mountsd` status lines to `status`.
- Added shell page selection:
  - `displaytest colors`
  - `displaytest font`
  - `displaytest safe`
  - `displaytest layout`
  - numeric aliases `displaytest 0` through `displaytest 3`
- Added auto menu app navigation:
  - VOL+/VOL- changes display test page
  - POWER returns to menu
- Added on-device changelog entry: `0.8.8 v77 DISPLAY TEST PAGES`.

## Artifacts

- `stage3/linux_init/init_v77`
  - SHA256 `534c77b5272fc484d263245abe711af769cadcc973c077d544032795ca9da935`
- `stage3/ramdisk_v77.cpio`
  - SHA256 `b0f4bd91d56f17772ff38b4013a849a6ba02099b517196a1009066499e35de4a`
- `stage3/boot_linux_v77.img`
  - SHA256 `176602ad6962dd298df3fc9090aefb335104e3eca496d8f75d6ec1d466dacaea`

## Validation

- Static ARM64 build — PASS
- v77 ramdisk and boot image generation — PASS
- boot image marker strings:
  - `A90 Linux init 0.8.8 (v77)`
  - `A90v77`
  - `0.8.8 v77 DISPLAY TEST PAGES`
- native init v76 → TWRP recovery → boot partition flash → v77 boot — PASS
- `native_init_flash.py ... --verify-protocol auto` verified `cmdv1 version/status` with `rc=0`, `status=ok`.
- Bridge display page validation:
  - `displaytest colors` → `rc=0`, `status=ok`
  - `displaytest font` → `rc=0`, `status=ok`
  - `displaytest safe` → `rc=0`, `status=ok`
  - `displaytest layout` → `rc=0`, `status=ok`
- Cutout calibration validation:
  - `cutoutcal` → `x=540 y=80 size=49`, `rc=0`, `status=ok`
  - `cutoutcal 540 80 49` → `rc=0`, `status=ok`
  - `displaytest safe` now renders the same calibration reference and returns `rc=0`, `status=ok`
- SD workspace validation:
  - `mkfs.ext4 -F -L A90_NATIVE /dev/block/mmcblk0p1` — PASS
  - `blkid /dev/block/mmcblk0p1` → `LABEL="A90_NATIVE"`, `TYPE="ext4"`
  - `mountsd init` created `/mnt/sdext/a90/{bin,logs,tmp,rootfs,images,backups}`
  - write/sync/read probe at `/mnt/sdext/a90/tmp/mountsd_probe.txt` — PASS
  - `mountsd ro`, `mountsd off`, `mountsd status`, final `status` integration — PASS
- Restored `autohud 2`; final `status` showed `autohud: running`.

## Current Baseline

`0.8.8 (v77)` is now the latest verified native init baseline.

The v48 fallback image remains the known-good rescue path, and v49 remains an isolated failed experiment.
