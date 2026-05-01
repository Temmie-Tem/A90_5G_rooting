# Native Init v92 Shell Controller API Report (2026-05-02)

## Summary

- Build: `A90 Linux init 0.8.23 (v92)`
- Source: `stage3/linux_init/init_v92.c` + `stage3/linux_init/v92/*.inc.c`
- New modules: `stage3/linux_init/a90_shell.c/h`, `stage3/linux_init/a90_controller.c/h`
- Boot image: `stage3/boot_linux_v92.img`
- Goal: make shell result/metadata and menu-aware command gating explicit without changing command UX.
- Status: local build and static validation complete; device flash validation is pending.

## Changes

- Added `a90_shell.c/h` for command flags/types, last-result storage, protocol sequence allocation, command lookup, errno normalization, and result printing.
- Added `a90_controller.c/h` for serial hide-word detection and auto-menu / power-page busy policy.
- Updated v92 shell dispatch to call `a90_shell_*` and `a90_controller_*` APIs while keeping command handlers and command table entries in the include tree.
- Preserved nonblocking `screenmenu`, `hide`/`hidemenu`/`resume`, `blindmenu` rescue behavior, and raw-control reboot/recovery/poweroff behavior.
- Updated ABOUT/changelog UI entries for `0.8.23 v92 SHELL CONTROLLER API` while retaining v91 CPU stress helper detail.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v92` | `d2bffdd2111406a2c409a0a03f5605163e016f86cf775199856daf70cd8017f5` |
| `stage3/ramdisk_v92.cpio` | `1cd524c1ece925b3d5d70b7ee19a7247f1a40c00aab24535f165911fde335880` |
| `stage3/boot_linux_v92.img` | `817a6a9e2b6c7f1c64e28d972122cd4c3ab022a9430a74a0fbfbef9301079b23` |

## Validation

- Local static ARM64 init build with `-Wall -Wextra` — PASS
- `git diff --check` — PASS
- Host Python `py_compile` — PASS
- `readelf -d` static check for init — PASS
- Boot image markers: `A90 Linux init 0.8.23 (v92)`, `A90v92`, `0.8.23 v92 SHELL CONTROLLER API` — PASS
- Ramdisk contains `/init`, `/bin/a90sleep`, `/bin/a90_cpustress` — PASS
- v92 tree old direct shell helpers removed: `find_command`, `command_allowed_during_auto_menu`, `is_auto_menu_hide_word`, `shell_protocol_seq`, `save_last_result`, `print_shell_result` — PASS
- v92 dispatch uses `a90_shell_*` and `a90_controller_*` APIs — PASS

## Pending Device Validation

- Flash: `python3 scripts/revalidation/native_init_flash.py stage3/boot_linux_v92.img --from-native --expect-version "A90 Linux init 0.8.23 (v92)" --verify-protocol auto`
- Regression: `version`, `status`, `last`, `cmdv1 version/status`, unknown command framing, busy command framing, `screenmenu`, `hide`, menu-visible observation commands, power-page dangerous busy gate, `cpustress 3 2`, `autohud 2`, and `watchhud 1 2`.

## Notes

- Latest verified remains `A90 Linux init 0.8.22 (v91)` until v92 device flash validation passes.
- `stage3/boot_linux_v92.img` is a local ignored artifact prepared for the next flash step.
