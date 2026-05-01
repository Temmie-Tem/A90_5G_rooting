# Native Init v90 Metrics API Report (2026-05-02)

## Summary

- Build: `A90 Linux init 0.8.21 (v90)`
- Source: `stage3/linux_init/init_v90.c` + `stage3/linux_init/v90/*.inc.c`
- New module: `stage3/linux_init/a90_metrics.c/h`
- Boot image: `stage3/boot_linux_v90.img`
- Goal: move sensor/sysfs metric reads out of HUD and into a reusable metrics API.

## Changes

- Added `a90_metrics.c/h` for battery, CPU, GPU, memory, power, uptime, load, and CPU frequency labels.
- Removed `a90_hud_status_snapshot`, `a90_hud_read_status_snapshot()`, and `a90_hud_read_sysfs_long()` from the HUD public API.
- Updated status HUD, `status`, and CPU stress screen callsites to use `a90_metrics_*`.
- Preserved v89 menu control behavior, nonblocking `screenmenu`, displaytest, cutout calibration, storage, and shell protocol behavior.
- Updated version/changelog/kmsg markers to `0.8.21 (v90)` / `A90v90`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v90` | `106c1b7d28bf6d9d82042bc4f3588bc3045ec3e06534cdbc58213cf859e6f4c1` |
| `stage3/ramdisk_v90.cpio` | `66a2988105ab97db31154ab8e10ed5f11331adfee64bedcd9e95f20d7847295b` |
| `stage3/boot_linux_v90.img` | `0a968f4732a948e1994b4788d29e46e81d74c2dc4170417c4e4d198d6440beee` |

## Validation

- Local static ARM64 build with `-Wall -Wextra` — PASS
- `git diff --check` — PASS
- Host Python `py_compile` — PASS
- Boot image markers: `A90 Linux init 0.8.21 (v90)`, `A90v90`, `0.8.21 v90 METRICS API` — PASS
- Old HUD metrics API names removed from v90/shared HUD — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v90.img --from-native --expect-version "A90 Linux init 0.8.21 (v90)" --verify-protocol auto` — PASS
- Boot partition prefix readback: SHA256 matched `stage3/boot_linux_v90.img` — PASS
- Post-boot `cmdv1 version/status` — PASS
- Regression: `bootstatus`, `statushud`, `autohud 2`, `watchhud 1 2`, `screenmenu`, `hide`, `storage`, `mountsd status`, `logpath`, `timeline` — PASS
- Display/metrics regression: `cpustress 3 2`, `displaytest safe`, `cutoutcal` — PASS

## Notes

- `a90_metrics` intentionally depends only on common util/sysfs style helpers and does not depend on HUD/menu/shell/console.
- CPU usage still needs a previous `/proc/stat` sample, so the first sample may remain `?`; this preserves v89 behavior.
- Latest verified is now `A90 Linux init 0.8.21 (v90)`.
- Good next candidates are `helpers/a90_cpustress` externalization, shell/controller cleanup, or storage/netservice policy layering.
