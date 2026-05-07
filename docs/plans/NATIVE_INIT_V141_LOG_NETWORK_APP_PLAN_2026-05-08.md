# v141 Plan: LOG/NETWORK App Renderer Split

Date: `2026-05-08`
Target: `A90 Linux init 0.9.41 (v141)` / `0.9.41 v141 LOG NETWORK APP API`
Baseline: `A90 Linux init 0.9.40 (v140)`

## Summary

v141 continues low-risk UI/app ownership cleanup while cloud security scan results are pending. The target is the LOG and NETWORK summary screens that still rendered directly from `40_menu_apps.inc.c`.

## Scope

- Copy v140 into `init_v141.c` and `v141/*.inc.c`.
- Add `a90_app_log.c/h` for LOG summary rendering.
- Add `a90_app_network.c/h` for NETWORK summary rendering.
- Keep menu routing, netservice policy, exposure policy, and shell commands unchanged.

## Validation

- Static ARM64 build with `a90_app_log.c` and `a90_app_network.c`.
- Marker check for `A90 Linux init 0.9.41 (v141)`, `A90v141`, `0.9.41 v141 LOG NETWORK APP API`.
- Real-device flash and `cmdv1 version/status` verify.
- Integrated validation and 3-cycle quick soak.
- Local targeted security rescan.
