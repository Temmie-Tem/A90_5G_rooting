# Native Init v87 Input API Plan (2026-04-30)

## Summary

- Target: `A90 Linux init 0.8.18 (v87)`
- Theme: `0.8.18 v87 INPUT API`
- Goal: move physical button open/wait/gesture decode helpers into `a90_input.c/h` while keeping HUD/menu/displaytest behavior stable.
- Small UX fix: show boot summary time with 0.1s precision instead of truncated integer seconds.

## Implementation

- Copy v86 to `init_v87.c` + `v87/*.inc.c`, bump version/build/kmsg markers to v87.
- Add `a90_input.c/h` for input context open/close, key wait, gesture wait, decoder helpers, gesture names, menu-action mapping, and input layout printing.
- Replace v87 include-tree direct `key_wait_context`, key wait, and gesture decoder implementations with `a90_input_*` calls.
- Keep autoHUD/menu/app routing in `v87/40_menu_apps.inc.c`; v87 does not split `a90_hud.c/h` or `a90_menu.c/h`.
- Change `a90_timeline_boot_summary()` from `BOOT OK shell 3S` style truncation to `BOOT OK shell 4.0s` style rounded 0.1s display.

## Validation

- Build static ARM64 with `init_v87.c` plus existing shared modules and new `a90_input.c`.
- Verify boot image markers: `A90 Linux init 0.8.18 (v87)`, `A90v87`, `0.8.18 v87 INPUT API`.
- Static checks: `git diff --check`, host Python `py_compile`, and no old direct input wait/decoder implementation in `stage3/linux_init/v87`.
- Device checks after bridge recovery: flash `stage3/boot_linux_v87.img`, then verify `version`, `status`, `bootstatus`, `inputlayout`, `waitkey`, `waitgesture`, `inputmonitor`, `screenmenu`, `blindmenu`, `displaytest safe`, `cutoutcal`, `autohud 2`.

## Notes

- Latest verified remains v86 until v87 is flashed and checked on the device.
- v88 candidate after v87 verification: HUD/menu layering split, with menu remaining the last and most coupled UI module.
