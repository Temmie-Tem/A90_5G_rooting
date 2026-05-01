# v92 Plan: Shell/Controller Cleanup

Date: `2026-05-02`

## Summary

- Target: `A90 Linux init 0.8.23 (v92)` / `0.8.23 v92 SHELL CONTROLLER API`
- Goal: make shell dispatch and menu busy policy explicit without changing command UX.
- Baseline: v91 is verified with external `/bin/a90_cpustress`, physical-button menu regression PASS, and nonblocking `screenmenu`.
- This plan is documentation only. Code, boot image, README latest verified, and changelog stay on v91 until v92 is flashed and verified.

## Current Shape

- `v91/80_shell_dispatch.inc.c` still owns command flags, command lookup, last result, raw dispatch, `cmdv1`, `cmdv1x`, busy gate, and the main shell loop.
- `screenmenu`/`hide` request helpers and power-page busy policy are now stable, but shell dispatch still knows too much about menu state.
- The command handlers are spread across the v91 include tree, so moving the full command table to a compiled module in one step would create avoidable visibility risk.

## Key Changes

- Copy v91 to `init_v92.c` and `v92/*.inc.c`, then update version, boot marker, ABOUT, and changelog strings.
- Add `a90_shell.c/h` as the small shell API layer for command flags/types, last-result storage, command lookup helpers, and result formatting helpers.
- Add `a90_controller.c/h` as the policy layer for menu-aware command gating: hide word detection, auto-menu allowed command checks, power-page dangerous-command blocking, and busy reason strings.
- Keep actual command handler bodies and the command table entries in the v92 include tree; v92 should call shell/controller APIs rather than move every command implementation.
- Preserve raw-control behavior for `reboot`, `recovery`, and `poweroff`; successful reboot-style commands may still cut the serial connection before a framed result.

## Test Plan

- Local build: static ARM64 build with v92 source plus existing modules and new `a90_shell.c` / `a90_controller.c`.
- Static checks: `git diff --check`, host Python `py_compile`, and `strings` markers for `A90 Linux init 0.8.23 (v92)`, `A90v92`, and `0.8.23 v92 SHELL CONTROLLER API`.
- Structure checks: confirm v92 shell dispatch uses `a90_shell_*` and `a90_controller_*`, while storage/netservice handlers and UI app bodies remain in the include tree.
- Device flash: `native_init_flash.py stage3/boot_linux_v92.img --from-native --expect-version "A90 Linux init 0.8.23 (v92)" --verify-protocol auto`.
- Regression: `version`, `status`, `last`, `cmdv1 version/status`, unknown command framing, busy command framing, `screenmenu` immediate return, menu-visible `status/logpath/timeline/storage`, power-page dangerous busy gate, `hide`/`hidemenu`/`resume`, `cpustress 3 2`, `autohud 2`, and `watchhud 1 2`.

## Assumptions

- v92 is structural cleanup, not a new user-facing feature.
- Storage/netservice policy split, command handler file-by-file split, full shell loop compiled-module migration, ADB, BusyBox, and dropbear remain v93+ candidates.
- `screenmenu` remains nonblocking, `blindmenu` remains blocking rescue foreground UI, and v91 menu/button behavior must remain unchanged.
