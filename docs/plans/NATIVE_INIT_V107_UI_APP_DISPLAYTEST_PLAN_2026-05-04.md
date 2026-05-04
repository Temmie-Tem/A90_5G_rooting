# Native Init v107 Plan: UI App Split 2 - Display Test

Date: `2026-05-04`
Baseline: `A90 Linux init 0.9.6 (v106)` after v106 validation
Target: `A90 Linux init 0.9.7 (v107)` / `0.9.7 v107 APP DISPLAYTEST API`

## Summary

- v107 continues the UI/App Architecture track after ABOUT/changelog split.
- Goal: move display-test and cutout-calibration screen rendering into a dedicated app module.
- This remains a structure-only refactor: no color/layout/cutout UX change unless required to fix an obvious regression.

## Key Changes

- Copy v106 to `init_v107.c` and `v107/*.inc.c`, then bump version/build/kmsg/changelog to v107.
- Add `stage3/linux_init/a90_app_displaytest.c/h`.
- Move display-oriented app rendering out of `v107/40_menu_apps.inc.c`:
  - `displaytest colors`
  - `displaytest font`
  - `displaytest safe`
  - `displaytest layout`
  - `cutoutcal` preview/rendering path
- Keep menu routing and command handler wrappers in the include tree unless moving them is required to compile.
- Public API should be small:
  - `a90_app_displaytest_draw(page)`
  - `a90_app_displaytest_draw_cutoutcal(...)`
  - optional page-name/parse helper if existing command routing needs it
- `a90_app_displaytest` may depend on KMS/draw/HUD layout primitives, but must not depend on shell dispatch, storage, netservice, or run/service policy.

## Validation

- Static build includes `a90_app_displaytest.c` and all v106 modules.
- Marker checks:
  - `A90 Linux init 0.9.7 (v107)`
  - `A90v107`
  - `0.9.7 v107 APP DISPLAYTEST API`
- `git diff --check` and host Python `py_compile` pass.
- Device validation after flash:
  - `version`, `status`, `bootstatus`, `selftest verbose`
  - `displaytest colors`, `displaytest font`, `displaytest safe`, `displaytest layout`
  - `cutoutcal`, current known-good cutout parameters, then `displaytest safe`
  - `screenmenu` display-test page navigation, then `hide`
  - `statushud`, `autohud 2`
  - quick soak with `native_soak_validate.py --cycles 3 --sleep 1`

## Acceptance

- All display-test pages render with v105/v106 visual behavior.
- Cutout calibration remains usable and does not shift safe-area unexpectedly.
- `v107/40_menu_apps.inc.c` no longer owns displaytest/cutout rendering internals.
- Report is written to `docs/reports/NATIVE_INIT_V107_UI_APP_DISPLAYTEST_2026-05-04.md` after validation.
