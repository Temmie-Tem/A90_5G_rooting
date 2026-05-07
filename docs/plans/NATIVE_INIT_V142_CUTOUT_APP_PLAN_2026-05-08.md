# v142 Plan: Cutout Calibration App API Split

Date: `2026-05-08`
Target: `A90 Linux init 0.9.42 (v142)` / `0.9.42 v142 CUTOUT APP API`
Baseline: `A90 Linux init 0.9.41 (v141)`

## Summary

v142 moves cutout calibration state and key-event handling out of the auto-HUD/menu include tree and into the displaytest app module. This keeps the interactive cutout UX unchanged while reducing controller-owned app state.

## Scope

- Copy v141 into `init_v142.c` and `v142/*.inc.c`.
- Extend `a90_app_displaytest.c/h` with cutout calibration state APIs.
- Replace include-tree cutout init/clamp/feed/draw wrappers with `a90_app_displaytest_cutout_*` calls.
- Keep displaytest/cutout command names and menu behavior unchanged.

## Validation

- Static ARM64 build.
- Real-device flash and `cmdv1 version/status` verify.
- Direct `displaytest safe` and `cutoutcal` command regression.
- Integrated validation, quick soak, and local targeted security rescan.
