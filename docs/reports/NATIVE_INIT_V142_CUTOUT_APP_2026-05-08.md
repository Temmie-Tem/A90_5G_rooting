# Native Init v142 Cutout Calibration App Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.42 (v142)` / `0.9.42 v142 CUTOUT APP API`
Baseline: `A90 Linux init 0.9.41 (v141)`

## Summary

- Extended `a90_app_displaytest.c/h` with cutout calibration default/clamp/reset/feed/draw APIs.
- Removed cutout calibration init/adjust/feed implementation from `v142/40_menu_apps.inc.c`.
- Updated `cutoutcal` shell handler to use the displaytest app API.
- Real-device flash, displaytest/cutout commands, integrated validation, quick soak, and local security rescan passed.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v142` | `6de702d7e92f7bd15ff3122b9dd58db66062e20f04b7c8c37bd8243f482353f9` |
| `stage3/ramdisk_v142.cpio` | `c8a33eceacc4373c71e0477c8630652ff9acde0f14c634317753c167a63bf23e` |
| `stage3/boot_linux_v142.img` | `6c9ed11bf580fb695e0e28d0777d00853b03f90a56338b2abc645532fd5f14e6` |

## Validation

- Static ARM64 build — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `displaytest safe` — PASS.
- `cutoutcal` — PASS.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- Cutout calibration physical button semantics are intended to remain unchanged: VOL adjusts, POWER cycles field, long/double power or VOL+DN exits.
- Manual physical-button cutout calibration can still be spot-checked if desired, but shell/display regressions are green.
