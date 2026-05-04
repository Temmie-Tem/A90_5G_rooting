# Native Init v107 UI App Displaytest Report

Date: `2026-05-04`
Version: `A90 Linux init 0.9.7 (v107)` / `0.9.7 v107 APP DISPLAYTEST API`
Baseline: `A90 Linux init 0.9.6 (v106)`

## Summary

- v107 continues the UI/App Architecture split after v106 ABOUT extraction.
- Added `a90_app_displaytest.c/h` and moved displaytest/cutout rendering out of `v107/40_menu_apps.inc.c`.
- Preserved displaytest/cutout UX, menu routing, storage/runtime/network policy, and `screenmenu` nonblocking behavior.
- Real-device flash, display command regression, and quick soak passed.

## Code Changes

- Added `stage3/linux_init/init_v107.c` and `stage3/linux_init/v107/*.inc.c` copied from v106.
- Updated `stage3/linux_init/a90_config.h` to `0.9.7` / `v107`.
- Added `stage3/linux_init/a90_app_displaytest.c` and `stage3/linux_init/a90_app_displaytest.h`.
- Kept cutout interaction state in the include tree, but moved cutout and displaytest framebuffer rendering behind `a90_app_displaytest_*` APIs.
- Updated ABOUT/changelog menu data for the v107 entry.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v107` | `4eca7cc8f19bd6220f6073c88732bba9e4d3724ac46212e22927955345384b08` |
| `stage3/ramdisk_v107.cpio` | `27fb66002d32a8433eac0ced6cdaaf93e16ee011799ce50a8a48606f813c1698` |
| `stage3/boot_linux_v107.img` | `365dab681ed9d83fa5dc44fa6c619da48de270e507ec6d430794c1b2a1a5ef32` |

## Static Validation

- Static ARM64 build with `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS.
- Marker strings in init and boot image — PASS:
  - `A90 Linux init 0.9.7 (v107)`
  - `A90v107`
  - `0.9.7 v107 APP DISPLAYTEST API`
- `git diff --check` — PASS.
- Host Python `py_compile` — PASS.
- v107 include tree no longer owns the old displaytest/cutout renderer internals; it keeps only thin wrappers — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v107.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.7 (v107)" \
  --verify-protocol auto
```

Result: PASS.

- Local image marker and SHA check — PASS.
- Recovery ADB push and remote SHA check — PASS.
- Boot partition prefix SHA matched `stage3/boot_linux_v107.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

Manual command regression:

- `version`, `status`, `bootstatus`, `selftest verbose` — PASS.
- `displaytest colors` — PASS, page `COLOR / PIXEL` presented.
- `displaytest font` — PASS, page `FONT / WRAP` presented.
- `displaytest safe` — PASS, page `SAFE / CUTOUT` presented through cutout renderer.
- `displaytest layout` — PASS, page `HUD / MENU` presented.
- `cutoutcal` — PASS, default calibration screen presented.
- `statushud`, `autohud 2`, `screenmenu`, `hide` — PASS.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.7 (v107)" \
  --out tmp/soak/v107-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- The flash script correctly handled an active background menu by issuing `hide` before recovery.
- v107 does not change Wi-Fi, storage, netservice, runtime, rshell, or CPU stress policy.
- Next planned step: v108 input monitor/layout UI split.
