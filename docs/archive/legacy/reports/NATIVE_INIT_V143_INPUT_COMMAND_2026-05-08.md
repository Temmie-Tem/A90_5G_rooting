# Native Init v143 Input Command Handler Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.43 (v143)` / `0.9.43 v143 INPUT COMMAND API`
Baseline: `A90 Linux init 0.9.42 (v142)`

## Summary

- Added `a90_input_cmd.c/h` for `waitkey`, `waitgesture`, and `inputlayout` shell command handlers.
- Removed those handlers from `v143/40_menu_apps.inc.c`; `inputmonitor` remains there because it still owns foreground HUD stop/restore behavior.
- Updated shell dispatch wrappers to call the new input command API.
- Real-device flash, targeted input command checks, integrated validation, quick soak, and local security rescan passed.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v143` | `9a6eeb8fd10ceebeff016e78c9e654784d58ac8bed7cb637448f9aa9edf47b6f` |
| `stage3/ramdisk_v143.cpio` | `cb61128357dce96b9bcd5c953081fbc11c4154faa794f4293c9d1fe231f2af08` |
| `stage3/boot_linux_v143.img` | `e43d18488c5873ad5acd1b5be5db63b11f21b4cd0bbf975c7eab4c2611831daa` |

## Validation

- Static ARM64 build — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `inputlayout` — PASS.
- `hide` — PASS.
- `version` — PASS.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- `waitkey` and `waitgesture` retain their blocking/cancel semantics; unattended validation avoids starting them without physical input or same-session cancel.
- `inputmonitor` remains the next input-app cleanup candidate because it still depends on foreground HUD lifecycle helpers.
