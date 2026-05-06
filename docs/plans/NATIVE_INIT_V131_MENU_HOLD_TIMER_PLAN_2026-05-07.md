# v131 Plan: Timer-Based Menu Hold Scroll

## Summary

v131 targets `A90 Linux init 0.9.31 (v131)` / `0.9.31 v131 MENU HOLD TIMER`.
The goal is to fix v130 hold-scroll on hardware that does not emit usable
`EV_KEY value=2` repeat events for volume buttons.

## Key Changes

- Keep v130 physical `VOLUP+VOLDOWN` back shortcut.
- Track volume key down/up state in the auto HUD/menu loop.
- Use monotonic timer repeat instead of relying on kernel key-repeat events.
- Start repeat after `450ms`, then repeat every `120ms` while the key remains
  pressed.
- Apply the same volume-step helper to menu movement and ABOUT/changelog page
  navigation.

## Test Plan

- Local static ARM64 build and `strings` marker verification.
- Repack `stage3/boot_linux_v131.img` from v130 boot image with v131 ramdisk.
- Static checks: host Python `py_compile`, shell `bash -n`, `git diff --check`.
- Device validation with `native_init_flash.py --from-native --verify-protocol auto`.
- Runtime regression: `status`, `selftest verbose`, `screenmenu`, menu-visible
  busy gate, `hide`, and post-hide `run /bin/a90sleep 1`.
- Manual UX check: hold VOL+/VOL- in changelog list and confirm continuous
  movement; press VOLUP+VOLDOWN for back/hide behavior.

## Assumptions

- A90 may not emit kernel repeat events for physical volume keys in this boot
  mode.
- Timer-based repeat must only run while a volume key is held and must stop on
  release or combo-back handling.
- This version does not alter command allowlist/busy-gate behavior.
