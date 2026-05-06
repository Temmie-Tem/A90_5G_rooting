# v130 Plan: Menu Hold Scroll + Physical Back

## Summary

v130 targets `A90 Linux init 0.9.30 (v130)` / `0.9.30 v130 MENU HOLD BACK`.
The goal is to finish the v129 changelog paging UX by adding a physical back
shortcut and hold-repeat scrolling without changing menu security policy.

## Key Changes

- Keep v129 changelog paging and shared `a90_changelog.c/h` data model.
- Treat volume `EV_KEY value=2` repeat events as repeated movement/page input.
- Add `VOLUP+VOLDOWN` handling in the auto HUD/menu loop:
  - active app: return to menu.
  - submenu: go back to parent page.
  - main menu: hide menu and return to HUD/log-tail.
- Keep POWER as select/back for existing screens and avoid repeat-triggered
  POWER selection.
- Update menu/about footer hints so the physical controls are discoverable.

## Test Plan

- Local static ARM64 build and `strings` marker verification.
- Repack `stage3/boot_linux_v130.img` from v129 boot image with v130 ramdisk.
- Static checks: host Python `py_compile`, shell `bash -n`, `git diff --check`.
- Device validation with `native_init_flash.py --from-native --verify-protocol auto`.
- Runtime regression: `status`, `selftest verbose`, `screenmenu`, menu-visible
  busy gate, `hide`, and post-hide `run /bin/a90sleep 1`.
- Manual UX check: hold VOL+/VOL- in changelog list and press VOLUP+VOLDOWN for
  back/hide behavior.

## Assumptions

- Hardware/input driver emits key repeat as `EV_KEY value=2` while holding
  volume buttons.
- If repeat is not emitted, single-click navigation remains unchanged.
- This version does not alter command allowlist/busy-gate behavior.
