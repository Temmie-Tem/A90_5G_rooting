# A90 Native Init Security F032 Hold Timer Fix

Date: 2026-05-07
Scope: retained v131-v133 auto-HUD menu source
Finding: `F032` volume hold timer spin in non-repeat screens

## Summary

A fresh Codex Cloud scan found a low-severity availability bug in the volume hold repeat timer introduced around v131. The bug was still present in retained v131, v132, and v133 source snapshots. The fix keeps repeat scrolling behavior on consumable screens and clears the hold timer when the current screen cannot consume repeat steps.

## Root Cause

The auto-HUD menu loop shortened `poll()` timeout to the pending hold-repeat deadline whenever `menu_hold_code` was non-zero. After the deadline, it advanced `menu_hold_next_ms` only when `auto_menu_handle_volume_step()` returned true. On non-repeat screens, the helper returned false and left the timer expired, which could cause repeated zero-timeout polls and redraws until key release.

## Changes

- Updated `stage3/linux_init/v131/40_menu_apps.inc.c`.
- Updated `stage3/linux_init/v132/40_menu_apps.inc.c`.
- Updated `stage3/linux_init/v133/40_menu_apps.inc.c`.
- Added F032 finding detail documentation.

## Behavior After Fix

| context | result |
|---|---|
| About/changelog screen with multiple pages | repeat step is consumed and timer is rescheduled |
| non-ABOUT active app | repeat step is not consumed and hold timer is cleared |
| single-page ABOUT context | repeat step is not consumed and hold timer is cleared |
| volume key release | existing release cleanup remains unchanged |

## Validation

- ARM64 static v133 syntax/build check to `/tmp/a90_init_v133_check` — PASS.
- `strings` marker check for `A90 Linux init 0.9.33 (v133)`, `A90v133`, and `0.9.33 v133 CHANGELOG SERIES` — PASS.
- Source pattern check confirms v131-v133 have the same defensive timeout branch.
- `git diff --check` — PASS.
- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py scripts/revalidation/local_security_rescan.py` — PASS.

## Notes

- This patch is retained-source maintenance and does not change latest verified boot image status by itself.
- v134 implementation should be copied from the patched v133 tree so the fix remains present in the next boot image.
