# v133 Plan: Changelog Series Navigation

## Summary

v133 targets `A90 Linux init 0.9.33 (v133)` / `0.9.33 v133 CHANGELOG SERIES`.
The goal is to reduce ABOUT/changelog list length by grouping entries by version
series before opening per-version detail screens.

This builds on v132's shared changelog table cleanup. It must not reintroduce
per-version enum/app render routes.

## Key Changes

- Copy v132 into `init_v133.c` and `v133/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.33` / `v133`.
- Add a v133 entry to `a90_changelog.c`.
- Add changelog series API in `a90_changelog.c/h`:
  - series count
  - series label/summary
  - series entry count
  - series-local index to global changelog index mapping
- Add a changelog series page in `a90_menu.c/h`:
  - `0.9.x RECENT`
  - `0.8.x LEGACY`
  - older groups as needed
- Keep the existing changelog detail renderer and feed it a global changelog
  index resolved from the selected series and row.

## Test Plan

- Build ARM64 static `stage3/linux_init/init_v133`.
- Repack `stage3/boot_linux_v133.img` from the v132 boot image with a v133
  ramdisk.
- Check strings markers for `A90 Linux init 0.9.33 (v133)`, `A90v133`, and
  `0.9.33 v133 CHANGELOG SERIES`.
- Run host harness for series count, first series label, version page mapping,
  and first entry detail index.
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
- Run `native_soak_validate.py` quick soak with v133 expected version.

## Assumptions

- Changelog entries remain ordered newest-first in the shared table.
- Series are derived from semantic version prefix, for example `0.9.33` ->
  `0.9.x`.
- Manual visual confirmation of the series list and v133 detail screen can be
  done as a follow-up from the device display.
