# Native Init v87 Input API Report (2026-04-30)

## Summary

- Build: `A90 Linux init 0.8.18 (v87)`
- Source: `stage3/linux_init/init_v87.c` + `stage3/linux_init/v87/*.inc.c`
- New module: `stage3/linux_init/a90_input.c/h`
- Boot image: `stage3/boot_linux_v87.img`
- Result: LOCAL PASS / DEVICE PENDING — local build, static checks, boot image generation, and marker checks passed; bridge returned timeout/reset before device flash validation.

## Changes

- Added `a90_input.c/h` for input context open/close, key wait, gesture wait, decoder helpers, gesture names, menu-action mapping, and input layout printing.
- Removed the old inline `key_wait_context`, key wait, and gesture decoder implementation from the v87 include tree.
- Updated waitkey/waitgesture/inputmonitor/screenmenu/blindmenu call sites to use `a90_input_*` API names.
- Updated version/changelog/kmsg markers to `0.8.18 (v87)` / `A90v87`.
- Updated boot summary formatting from integer seconds to rounded 0.1s seconds.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v87` | `122db3f8a089667fecab864e9e63d5ab65961da774ad20196820d74d5e124bc0` |
| `stage3/ramdisk_v87.cpio` | `5d6cc0825da26c3bb89b8b45741c06814df1933ce32902662577ecedb49dfdb6` |
| `stage3/boot_linux_v87.img` | `ad93b1bf69586a468e6fafdcf2045d1c6192b01dae96f02bc6b7c0edddb6a970` |

## Validation

- Local build: static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Static checks: no old direct `key_wait_context` / `open_key_wait_context` / `wait_for_input_gesture` implementation in v87 include tree — PASS
- Host script checks: `py_compile` for `a90ctl.py`, `native_init_flash.py`, `tcpctl_host.py`, `netservice_reconnect_soak.py` — PASS
- Boot image markers: `A90 Linux init 0.8.18 (v87)`, `A90v87`, `0.8.18 v87 INPUT API` — PASS
- Bridge availability probe: `a90ctl.py --timeout 3 version` — FAIL/PENDING (`A90P1 END` timeout and connection reset)
- Device flash: PENDING until bridge/device state is restored.

## Pending Device Regression

- Flash: `python3 scripts/revalidation/native_init_flash.py stage3/boot_linux_v87.img --from-native --expect-version "A90 Linux init 0.8.18 (v87)" --verify-protocol auto`
- Shell: `version`, `status`, `bootstatus`, `statushud`, `autohud 2`
- Input: `inputlayout`, `waitkey`, `waitgesture`, `inputmonitor 0`, `screenmenu`, `blindmenu`
- Display: `displaytest safe`, `cutoutcal`, `kmsframe`, menu busy gate, q/Ctrl-C cancel

## Notes

- Latest verified remains `A90 Linux init 0.8.17 (v86)` until v87 device validation passes.
- v87 intentionally keeps menu/HUD/displaytest policy in the include tree. The next split should happen only after input regressions pass on-device.
