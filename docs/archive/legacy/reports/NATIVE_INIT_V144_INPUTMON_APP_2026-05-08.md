# Native Init v144 Inputmonitor Foreground App Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.44 (v144)` / `0.9.44 v144 INPUTMON APP API`
Baseline: `A90 Linux init 0.9.43 (v143)`

## Summary

- Added `a90_app_inputmon_run_foreground()` and foreground lifecycle hooks to `a90_app_inputmon.c/h`.
- Removed the `inputmonitor` foreground poll/read/cancel loop from `v144/40_menu_apps.inc.c`.
- Kept auto-HUD stop/restore behavior as include-tree callbacks because those helpers still own the HUD child lifecycle.
- Real-device flash, direct `inputmonitor 0` q cancel, integrated validation, quick soak, and local security rescan passed.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v144` | `c3b24f41db773a34a37216192772b1752c4309b06e95b398a9c8b5cd3ab6e705` |
| `stage3/ramdisk_v144.cpio` | `c8f6b3f65f06741a9811f5d110e532c217f2c5cd55d842605c1512cdf34d974d` |
| `stage3/boot_linux_v144.img` | `61168fa6867d44676895ef8aae789ca115347d893b280fbffe16194affe47302` |

## Validation

- Static ARM64 build — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `inputmonitor 0` followed by `q` — PASS, returned framed `rc=-125` cancel result.
- `inputlayout` — PASS.
- `hide` — PASS.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- `inputmonitor` still intentionally blocks as a foreground display command until event count, all-buttons exit, or q/Ctrl-C cancel.
- The next validation-focused step is to automate `waitkey`/`waitgesture` q cancel coverage without needing physical button input.
