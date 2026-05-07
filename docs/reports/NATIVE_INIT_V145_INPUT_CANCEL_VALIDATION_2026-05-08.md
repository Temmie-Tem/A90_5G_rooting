# Native Init v145 Input Cancel Validation Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.45 (v145)` / `0.9.45 v145 INPUT CANCEL HARNESS`
Baseline: `A90 Linux init 0.9.44 (v144)`

## Summary

- Added `scripts/revalidation/native_input_cancel_validate.py`.
- The harness verifies blocking input commands by starting `cmdv1`, waiting for a start marker, sending `q`, and requiring `A90P1 END rc=-125 status=error`.
- Verified `waitkey 1`, `waitgesture 1`, and `inputmonitor 0` q-cancel paths on real hardware.
- Real-device flash, input cancel harness, integrated validation, quick soak, and local security rescan passed.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v145` | `952eacce8102a5c839c914a4087872845418582e4c3f484d96484bac2a0223e6` |
| `stage3/ramdisk_v145.cpio` | `b98f859874f09febfca163cbc1816341dd1514daa9819883c133dbd0e0c7b07d` |
| `stage3/boot_linux_v145.img` | `568ec0b2b45c1852b56bd08c6e5d2ef42bf817b7dd5b3a0f9746ce90a06cad67` |

## Validation

- Static ARM64 build — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_input_cancel_validate.py` — `PASS cases=3/3`.
- `waitkey 1` q cancel — PASS, `rc=-125 status=error`.
- `waitgesture 1` q cancel — PASS, `rc=-125 status=error`.
- `inputmonitor 0` q cancel — PASS, `rc=-125 status=error`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- v145 is validation/tooling focused; device-side blocking input UX is intended to remain unchanged.
- This closes the pre-network validation gap for q-cancel behavior of foreground/blocking input commands.
