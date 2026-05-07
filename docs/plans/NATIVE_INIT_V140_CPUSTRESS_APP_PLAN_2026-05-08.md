# v140 Plan: CPU Stress App Module Split

Date: `2026-05-08`
Target: `A90 Linux init 0.9.40 (v140)` / `0.9.40 v140 CPUSTRESS APP API`
Baseline: `A90 Linux init 0.9.39 (v139)`

## Summary

v140 keeps network-facing changes on hold while the fresh cloud scan is pending and uses the available development time for a low-risk UI/app ownership split. The target is the CPU stress screen app, because it is self-contained and still had helper process lifecycle and screen renderer code inside `v139/40_menu_apps.inc.c`.

## Scope

- Copy v139 into `init_v140.c` and `v140/*.inc.c`.
- Add `a90_app_cpustress.c/h`.
- Move CPU stress app helper spawn/reap/stop, timeout cleanup, and renderer into the new app module.
- Keep shell `cpustress`, menu routing, button semantics, controller policy, netservice, rshell, storage, and exposure policy unchanged.
- Ensure the v140 ramdisk contains `/bin/a90_cpustress` and `/bin/a90_rshell` helpers.

## Non-Goals

- No broader network exposure.
- No Wi-Fi bring-up.
- No menu UX redesign.
- No long unattended soak in the active work window.

## Validation

- Static ARM64 build with `a90_app_cpustress.c` included.
- `strings` markers for `A90 Linux init 0.9.40 (v140)`, `A90v140`, and `0.9.40 v140 CPUSTRESS APP API`.
- `git diff --check` and host Python `py_compile`.
- Real-device flash with `native_init_flash.py`.
- Direct `cpustress 3 2` command regression.
- `native_integrated_validate.py` and 3-cycle quick soak.
- Local targeted security rescan.

## Acceptance

- v140 boots and verifies through `cmdv1 version/status`.
- CPU stress helper is present in the ramdisk and shell `cpustress 3 2` returns `rc=0`.
- `screenmenu` remains nonblocking and `hide` works.
- Local targeted security rescan has `FAIL=0`.
