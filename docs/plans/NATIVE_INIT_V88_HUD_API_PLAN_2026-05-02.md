# Native Init v88 HUD API Plan (2026-05-02)

## Summary

- Target: `A90 Linux init 0.8.19 (v88)`
- Theme: `0.8.19 v88 HUD API`
- Goal: move boot splash, status HUD, boot summary, warning/status display, and log tail panel drawing into `a90_hud.c/h`.
- Scope is HUD-first UI layering only. `screenmenu`, `blindmenu`, app routing, displaytest, cutoutcal, and inputmonitor screen logic stay in the v88 include tree.

## Implementation

- Copy v87 to `init_v88.c` + `v88/*.inc.c`, then bump version/build/kmsg/changelog markers to v88.
- Add `a90_hud.c/h` with small public APIs for status HUD, boot splash, log tail, warning/status message, and boot summary drawing.
- Replace direct v88 include-tree HUD/boot-splash/log-tail drawing helpers with `a90_hud_*` calls while preserving the current visual layout.
- Keep menu/app state machines and screen routing in `v88/40_menu_apps.inc.c`; v88 does not split `a90_menu.c/h`.
- Enforce dependency direction: `hud -> kms/draw/metrics/storage/timeline/log` is allowed; `hud -> menu`, `input -> menu`, and `draw -> hud` are not allowed.

## Candidate APIs

- `a90_hud_draw_status()` — draw the current sensor/status HUD once.
- `a90_hud_draw_boot_splash()` — draw the boot splash and return a normal command-style rc.
- `a90_hud_draw_log_tail()` — draw the native log tail panel into the active framebuffer.
- `a90_hud_draw_warning(const char *message)` — draw storage/fallback or other warning text.
- `a90_hud_show_boot_summary()` — draw or format the boot summary using timeline state.

## Validation

- Build static ARM64 with `init_v88.c`, existing shared modules, and new `a90_hud.c`.
- Verify boot image markers: `A90 Linux init 0.8.19 (v88)`, `A90v88`, `0.8.19 v88 HUD API`.
- Static checks: `git diff --check`, host Python `py_compile`, and `rg` checks showing core HUD/boot-splash/log-tail implementation moved behind `a90_hud_*`.
- Device checks: flash `stage3/boot_linux_v88.img`, then verify `version`, `status`, `bootstatus`, `statushud`, `autohud 2`, `watchhud 1 2`, `displaytest safe`, `screenmenu`, and `hide`.
- Regression criteria: v87 visual behavior remains stable, boot splash still transitions to HUD/menu, menu busy gate remains intact, and q/Ctrl-C cancel still works.

## Notes

- Latest verified remains `A90 Linux init 0.8.18 (v87)` until v88 is flashed and checked on the device.
- v88 is a refactor, not a user-facing feature release.
- If HUD extraction exposes too much menu coupling, stop at boot splash/status HUD/log tail and leave warning/status screens in the include tree for v89.
- Expected report after implementation: `docs/reports/NATIVE_INIT_V88_HUD_API_2026-05-02.md`.
