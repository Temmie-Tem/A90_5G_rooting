# A90 Native Init Security F033 Mountsd Menu Policy Fix

Date: 2026-05-07
Scope: shared controller menu busy-gate policy
Finding: `F033` menu policy allows bare `mountsd` side effects

## Summary

A fresh Codex Cloud scan found a low-severity policy bug in the menu-active command gate. Bare `mountsd` was treated as a safe status query, but the storage command defaults bare `mountsd` to `ro` and can remount the SD card read-only. The fix makes `mountsd` require an explicit `status` subcommand while the menu is active.

## Root Cause

`a90_controller_command_busy_reason_ex()` groups `mountsd`, `hudlog`, and `netservice` under `subcmd_absent_or_one_of(..., status)`. That helper intentionally allows absent subcommands for commands whose default behavior is read-only status. `hudlog` and `netservice` meet that contract; `mountsd` does not because `a90_storage_cmd_mountsd()` sets `mode = argc > 1 ? argv[1] : "ro"`.

## Changes

- Added `subcmd_one_of()` in `stage3/linux_init/a90_controller.c`.
- Changed `mountsd` menu-active allow policy to require exactly `mountsd status`.
- Left normal non-menu `mountsd` behavior unchanged.
- Added F033 finding detail documentation.
- Extended local targeted security rescan with a mountsd menu-policy check.

## Behavior After Fix

| command while menu visible | result |
|---|---|
| `mountsd status` | allowed |
| `mountsd` | blocked as menu busy |
| `mountsd ro` | blocked as menu busy |
| `mountsd rw` | blocked as menu busy |
| `hudlog` | still allowed as status |
| `netservice` | still allowed as status |

## Validation

- ARM64 static v133 syntax/build check to `/tmp/a90_init_v133_check` — PASS.
- `strings` marker check for `A90 Linux init 0.9.33 (v133)`, `A90v133`, and `0.9.33 v133 CHANGELOG SERIES` — PASS.
- Source pattern check confirms `mountsd` uses explicit-subcommand policy.
- `python3 scripts/revalidation/local_security_rescan.py --out docs/security/scans/SECURITY_FRESH_SCAN_V133_2026-05-07.md` — PASS.
- `git diff --check` — PASS.
- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py scripts/revalidation/local_security_rescan.py` — PASS.

## Notes

- This is a shared-controller fix, so future builds using `a90_controller.c` inherit the policy.
- This does not change the intentionally side-effecting `mountsd` behavior when the menu busy gate is inactive.
