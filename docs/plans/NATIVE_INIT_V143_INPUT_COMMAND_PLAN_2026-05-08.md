# v143 Plan: Input Command Handler API Split

Date: `2026-05-08`
Target: `A90 Linux init 0.9.43 (v143)` / `0.9.43 v143 INPUT COMMAND API`
Baseline: `A90 Linux init 0.9.42 (v142)`

## Summary

v143 moves the safe input shell command handlers out of the auto-HUD/menu include tree and into `a90_input_cmd.c/h`. The goal is to reduce `40_menu_apps.inc.c` residue without changing physical-button UX or foreground input monitor behavior.

## Scope

- Copy v142 into `init_v143.c` and `v143/*.inc.c`.
- Add `a90_input_cmd.c/h` for `waitkey`, `waitgesture`, and `inputlayout` command handlers.
- Replace shell dispatch wrappers with calls to `a90_input_cmd_*` APIs.
- Keep `inputmonitor` in the include tree because it still coordinates foreground HUD lifecycle.
- Keep menu, gesture decoding, and input device APIs unchanged.

## Validation

- Static ARM64 build.
- Real-device flash and `cmdv1 version/status` verify.
- Direct `inputlayout`, `hide`, and `version` command regression.
- Integrated validation, quick soak, and local targeted security rescan.
