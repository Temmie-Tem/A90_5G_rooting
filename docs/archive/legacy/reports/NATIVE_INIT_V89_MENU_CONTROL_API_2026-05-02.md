# Native Init v89 Menu Control API Report (2026-05-02)

## Summary

- Build: `A90 Linux init 0.8.20 (v89)`
- Source: `stage3/linux_init/init_v89.c` + `stage3/linux_init/v89/*.inc.c`
- New module: `stage3/linux_init/a90_menu.c/h`
- Boot image: `stage3/boot_linux_v89.img`
- Result: PASS — local build, static checks, boot image generation, TWRP flash, post-boot cmdv1 verify, nonblocking `screenmenu`, and noninteractive display/storage regressions passed.

## Changes

- Added `a90_menu.c/h` for menu page/action/app enums, item/page tables, menu state movement, action-to-app mapping, and CPU stress duration mapping.
- Changed `screenmenu`/`menu` from foreground blocking commands into background HUD menu show requests.
- Added formal `hide`, `hidemenu`, and `resume` commands that send a HUD menu hide request and return framed cmdv1 results.
- Extended `AUTO_MENU_REQUEST_PATH` IPC from hide-only to `show`/`hide`.
- Kept `blindmenu` as the blocking rescue foreground menu for display/HUD failure cases.
- Preserved displaytest, cutoutcal, inputmonitor, about/changelog, and CPU stress screen implementations in the v89 include tree.
- Updated version/changelog/kmsg markers to `0.8.20 (v89)` / `A90v89`.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v89` | `516d3b0c93104c00a0a5d9a8633cfe7041a75b7cfcf35871d65cb9ccbefe689f` |
| `stage3/ramdisk_v89.cpio` | `2a702cfdbe82633407583137dc5871b1a0911565cea1f3fcc1cfe0141cd2628e` |
| `stage3/boot_linux_v89.img` | `57a6b5b5a9091c5fe0339e5359ec34e68af00f040c64dfc902636aaedbc618ba` |

## Validation

- Local build: static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Static checks: `git diff --check` and host Python `py_compile` — PASS
- Boot image markers: `A90 Linux init 0.8.20 (v89)`, `A90v89`, `0.8.20 v89 MENU CONTROL API` — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v89.img --from-native --expect-version "A90 Linux init 0.8.20 (v89)" --verify-protocol auto` — PASS
- Boot partition prefix readback: SHA256 matched `stage3/boot_linux_v89.img` — PASS
- Post-boot cmdv1 verify: `version` and `status` rc=0/status=ok — PASS
- Nonblocking menu regression: `screenmenu` returned immediately with `rc=0`, `status=ok`, `duration_ms=0` — PASS
- Menu-visible command regression: `status`, `logpath`, `timeline`, and `storage` responded while the menu was active — PASS
- Hide command regression: `hide` returned `rc=0`, `status=ok` and requested HUD/log-tail mode — PASS
- Display/HUD regression: `bootstatus`, `statushud`, `autohud 2`, `displaytest safe`, `cutoutcal`, and `watchhud 1 2` — PASS

## Manual Follow-up

- Optional physical-button pass: use actual VOL+/VOL-/POWER presses in the background menu to verify move/select/back/hide flow.
- Optional rescue pass: run `blindmenu` only when ready to exit with physical buttons, because it intentionally remains foreground/blocking.
- Optional power-page pass: enter POWER page with physical buttons and confirm dangerous-command busy gate still blocks destructive commands until `hide`.

## Notes

- Latest verified is now `A90 Linux init 0.8.20 (v89)`.
- v89 removes the biggest shell-concurrency pain point: the normal screen menu no longer owns the serial shell loop.
- The next split can target a smaller `shell/controller` cleanup, `metrics` extraction, or `helpers/a90_cpustress` external process separation.
