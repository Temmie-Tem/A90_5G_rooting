# v132 Plan: Changelog Cleanup

## Summary

v132 targets `A90 Linux init 0.9.32 (v132)` / `0.9.32 v132 CHANGELOG CLEANUP`.
The goal is to remove the remaining legacy per-version ABOUT/changelog routes and
keep the UI on the shared `a90_changelog.c/h` data table introduced by v129.

This is a cleanup release. It does not change menu security policy, physical
button handling, shell protocol, storage, USB, or networking behavior.

## Key Changes

- Copy v131 into `init_v132.c` and `v132/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.32` / `v132`.
- Add a v132 changelog entry to `a90_changelog.c`.
- Remove legacy numeric changelog menu/app enum entries from `a90_menu.h`.
- Remove legacy changelog action-to-app routing from `a90_menu.c`.
- Remove legacy per-version draw functions and fallback routing from
  `a90_app_about.c`.
- Keep only the shared changelog list/detail index path:
  - `SCREEN_MENU_CHANGELOG_ENTRY`
  - `SCREEN_APP_CHANGELOG_DETAIL`
  - `a90_app_about_draw_changelog_detail_index()`

## Test Plan

- Build ARM64 static `stage3/linux_init/init_v132`.
- Repack `stage3/boot_linux_v132.img` from the v131 boot image with a v132
  ramdisk.
- Check strings markers for `A90 Linux init 0.9.32 (v132)`, `A90v132`, and
  `0.9.32 v132 CHANGELOG CLEANUP`.
- Run a host harness for changelog count, first entry, and app route behavior.
- Run static checks:
  - host Python `py_compile`
  - repository shell `bash -n`
  - `git diff --check`
- Flash through native bridge/TWRP with `native_init_flash.py --from-native`.
- Runtime regression:
  - `status`
  - `selftest verbose`
  - `screenmenu`
  - menu-visible busy gate for `run /bin/a90sleep 1`
  - `hide`
  - post-hide `run /bin/a90sleep 1`
- Run `native_soak_validate.py` quick soak with v132 expected version.

## Assumptions

- Historical `vXX` include snapshots remain retained as source history, but the
  latest active ABOUT/changelog implementation uses the shared table only.
- v132 does not attempt to rewrite old changelog prose; it removes duplicate UI
  routing paths first.
- Manual visual confirmation of the latest ABOUT/changelog entry can be done as
  a follow-up from the physical device screen.
