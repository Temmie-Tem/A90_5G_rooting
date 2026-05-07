# v144 Plan: Inputmonitor Foreground App API Split

Date: `2026-05-08`
Target: `A90 Linux init 0.9.44 (v144)` / `0.9.44 v144 INPUTMON APP API`
Baseline: `A90 Linux init 0.9.43 (v143)`

## Summary

v144 moves the `inputmonitor` foreground command loop out of the auto-HUD/menu include tree and into `a90_app_inputmon.c/h`. The include tree keeps only the lifecycle callbacks needed to stop and restore auto-HUD around a foreground display command.

## Scope

- Copy v143 into `init_v144.c` and `v144/*.inc.c`.
- Add `struct a90_app_inputmon_foreground_hooks` and `a90_app_inputmon_run_foreground()`.
- Replace the local `cmd_inputmonitor()` loop with a thin callback bridge.
- Preserve `inputmonitor [events]` UX, all-buttons exit behavior, and q/Ctrl-C cancel behavior.
- Keep auto-HUD/menu input app rendering behavior unchanged.

## Validation

- Static ARM64 build.
- Real-device flash and `cmdv1 version/status` verify.
- Direct `inputmonitor 0` q cancel regression.
- Direct `inputlayout` and `hide` regression.
- Integrated validation, quick soak, and local targeted security rescan.
