# Native Init v86 KMS/Draw API Report (2026-04-30)

## Summary

- Build: `A90 Linux init 0.8.17 (v86)`
- Source: `stage3/linux_init/init_v86.c` + `stage3/linux_init/v86/*.inc.c`
- New modules: `stage3/linux_init/a90_kms.c/h`, `stage3/linux_init/a90_draw.c/h`
- Boot image: `stage3/boot_linux_v86.img`
- Result: PASS — TWRP flash, post-boot `cmdv1 version/status`, KMS/draw regressions, screenmenu q cancel, and inputmonitor q cancel verified.

## Changes

- Added `a90_kms.c/h` for DRM/KMS dumb-buffer state, frame begin/present, framebuffer info, and probe output.
- Added `a90_draw.c/h` for framebuffer clear/rect/text/text-fit/outline/test-pattern primitives.
- Removed direct `kms_state` and `struct kms_display_state` ownership from the v86 include tree.
- Updated `cmd_version`/`cmd_status` to use `a90_kms_info()` instead of direct framebuffer state.
- Kept HUD/menu/input/displaytest policy in the v86 include tree to avoid behavior drift.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v86` | `e3d5e777a3825fa2c5212ab8b7de2fda74b8ced05881b82d75a666fa58ef1e81` |
| `stage3/ramdisk_v86.cpio` | `6d69aa340162c6a3279d2fa73a10452b50bb5956814da9bdc73524e85e06ebdd` |
| `stage3/boot_linux_v86.img` | `ca9991061edd1a7a1f33e61ebdbd61df4be5ce7bd9e3d3c5d23351b0c03afbc3` |

## Validation

- Local build: static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Static checks: no direct `kms_state` / `struct kms_display_state` in v86 include tree — PASS
- Host script checks: `py_compile` for `a90ctl.py`, `native_init_flash.py`, `tcpctl_host.py`, `netservice_reconnect_soak.py` — PASS
- Boot image markers: `A90 Linux init 0.8.17 (v86)`, `A90v86`, `0.8.17 v86 KMS DRAW API` — PASS
- Flash: native bridge → TWRP → boot partition write/readback → v86 boot — PASS
- Post-boot verify: `cmdv1 version/status`, `rc=0`, `status=ok` — PASS
- Display regression:
  - `kmsprobe` — PASS
  - `kmssolid blue`, `kmsframe`, `statushud` — PASS
  - `displaytest colors/font/safe/layout` — PASS
  - `cutoutcal` — PASS
  - `autohud 2` and final `status` — PASS
- Blocking regression:
  - raw `screenmenu` then `q` cancel — PASS
  - raw `inputmonitor 0` then `q` cancel — PASS

## Notes

- v86 intentionally does not split `a90_hud.c/h`, `a90_input.c/h`, or `a90_menu.c/h` yet.
- The next safest module candidate is v87 HUD or input split; menu should remain last because it depends on display, input, shell, logging, and app screens.
