# Native Init v108 Plan: UI App Split 3 - Input Monitor

Date: `2026-05-04`
Baseline: `A90 Linux init 0.9.7 (v107)` after v107 validation
Target: `A90 Linux init 0.9.8 (v108)` / `0.9.8 v108 APP INPUTMON API`

## Summary

- v108 completes the first UI/App split batch by separating input monitor and input layout UI.
- Goal: move input-focused app rendering/monitor screens into a dedicated module while keeping the existing `a90_input.c/h` low-level API unchanged.
- This is a refactor. Gesture semantics, menu actions, and physical button behavior must stay identical.

## Key Changes

- Copy v107 to `init_v108.c` and `v108/*.inc.c`, then bump version/build/kmsg/changelog to v108.
- Add `stage3/linux_init/a90_app_inputmon.c/h`.
- Move input-focused UI out of `v108/40_menu_apps.inc.c`:
  - input layout display
  - input monitor screen rendering
  - waitgesture/waitkey visual feedback if currently owned by the menu app block
- Keep low-level event open/poll/decode in `a90_input.c/h`; do not merge app UI into input core.
- Public API should be small:
  - `a90_app_inputmon_draw_layout()`
  - `a90_app_inputmon_run_monitor(events_or_seconds)`
  - `a90_app_inputmon_draw_event(...)` only if needed for monitor reuse
- `a90_app_inputmon` may call `a90_input` and draw/HUD primitives, but must not call shell dispatch, storage, netservice, or run/service policy.

## Validation

- Static build includes `a90_app_inputmon.c` and all v107 modules.
- Marker checks:
  - `A90 Linux init 0.9.8 (v108)`
  - `A90v108`
  - `0.9.8 v108 APP INPUTMON API`
- `git diff --check` and host Python `py_compile` pass.
- Device validation after flash:
  - `version`, `status`, `bootstatus`, `selftest verbose`
  - `inputlayout`
  - `waitkey`
  - `waitgesture`
  - `inputmonitor 0` or bounded monitor command
  - physical VOL+/VOL-/POWER single, double, long, and combo spot checks
  - `screenmenu` navigation, then `hide`
  - quick soak with `native_soak_validate.py --cycles 3 --sleep 1`

## Acceptance

- Physical button behavior matches v105-v107.
- Input monitor remains useful for press/release/duration/gesture tracing.
- `v108/40_menu_apps.inc.c` no longer owns input monitor/layout UI internals.
- Report is written to `docs/reports/NATIVE_INIT_V108_UI_APP_INPUTMON_2026-05-04.md` after validation.
