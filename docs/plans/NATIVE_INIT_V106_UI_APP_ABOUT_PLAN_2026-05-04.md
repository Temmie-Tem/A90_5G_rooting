# Native Init v106 Plan: UI App Split 1 - About/Changelog

Date: `2026-05-04`
Baseline: `A90 Linux init 0.9.5 (v105)`
Target: `A90 Linux init 0.9.6 (v106)` / `0.9.6 v106 APP ABOUT API`

## Summary

- v106 starts the post-v105 UI/App Architecture track.
- Goal: split low-risk ABOUT/version/changelog screen rendering out of `v106/40_menu_apps.inc.c` into a compiled module.
- This is a structure-only refactor: no menu UX change, no new app feature, no storage/network/runtime policy change.
- The implementation must preserve v105 behavior and keep `screenmenu` nonblocking.

## Key Changes

- Copy v105 to `init_v106.c` and `v106/*.inc.c`, then bump version/build/kmsg/changelog to v106.
- Add `stage3/linux_init/a90_app_about.c/h`.
- Move ABOUT-related rendering into the new module:
  - version/about screen
  - changelog list screen
  - changelog detail screen currently handled by the ABOUT app path
- Keep menu state, input handling, app routing, displaytest, inputmonitor, CPU stress, service/network app screens in `v106/40_menu_apps.inc.c`.
- Public API should be small:
  - `a90_app_about_draw_version()`
  - `a90_app_about_draw_changelog()`
  - `a90_app_about_draw_changelog_detail(page)`
- `a90_app_about` may depend on `a90_config`, `a90_draw`/existing screen drawing helpers exposed by include tree if needed, but must not call shell, run, storage, netservice, or input policy.
- If existing drawing helpers are still static in the include tree, expose only the minimal wrapper needed from the include tree rather than moving all drawing code.

## Validation

- Static build includes `a90_app_about.c` with the same v105 module set.
- Marker checks:
  - `A90 Linux init 0.9.6 (v106)`
  - `A90v106`
  - `0.9.6 v106 APP ABOUT API`
- `git diff --check` and host Python `py_compile` pass.
- Stale marker scan confirms no current-version v105 strings in `init_v106.c`, `v106/*.inc.c`, or `a90_config.h`.
- Device validation after flash:
  - `version`, `status`, `bootstatus`, `selftest verbose`
  - `screenmenu`, navigate to ABOUT/version/changelog/detail, then `hide`
  - `statushud`, `autohud 2`, `diag`, `runtime`, `storage`
  - `native_soak_validate.py --cycles 3 --sleep 1 --expect-version "A90 Linux init 0.9.6 (v106)"`

## Acceptance

- ABOUT and changelog screens look and navigate the same as v105.
- `v106/40_menu_apps.inc.c` loses ABOUT/changelog implementation responsibility.
- No behavior drift in shell, storage, Wi-Fi gate, netservice, or CPU stress.
- Report is written to `docs/reports/NATIVE_INIT_V106_UI_APP_ABOUT_2026-05-04.md` only after real-device validation passes.
