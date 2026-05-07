# v145 Plan: Input Cancel Validation Harness

Date: `2026-05-08`
Target: `A90 Linux init 0.9.45 (v145)` / `0.9.45 v145 INPUT CANCEL HARNESS`
Baseline: `A90 Linux init 0.9.44 (v144)`

## Summary

v145 adds a host-side validation harness for blocking input commands. The goal is to prove `waitkey`, `waitgesture`, and the v144 `inputmonitor` foreground path can be started and cancelled over the serial bridge without requiring physical button input or leaving the shell blocked.

## Scope

- Copy v144 into `init_v145.c` and `v145/*.inc.c` with version/changelog bump.
- Add `scripts/revalidation/native_input_cancel_validate.py`.
- Use one bridge connection per blocking command, send `cmdv1 <command>`, wait for the command-specific start marker, send `q`, and require framed cancel result `rc=-125`.
- Preserve device-side input behavior; this version is validation/tooling focused.

## Validation

- Static ARM64 build.
- Real-device flash and `cmdv1 version/status` verify.
- `native_input_cancel_validate.py` for `waitkey 1`, `waitgesture 1`, and `inputmonitor 0`.
- Integrated validation, quick soak, and local targeted security rescan.
