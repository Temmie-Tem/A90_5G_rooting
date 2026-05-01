# Native Init v88 HUD API Report (2026-05-02)

## Summary

- Build: `A90 Linux init 0.8.19 (v88)`
- Source: `stage3/linux_init/init_v88.c` + `stage3/linux_init/v88/*.inc.c`
- New module: `stage3/linux_init/a90_hud.c/h`
- Boot image: `stage3/boot_linux_v88.img`
- Result: PASS — local build, static checks, boot image generation, TWRP flash, post-boot cmdv1 verify, and noninteractive HUD/storage regressions passed.

## Changes

- Added `a90_hud.c/h` for boot splash lines/rendering, status HUD rendering, status snapshot reads, and log tail panel rendering.
- Replaced v88 include-tree direct `kms_draw_status_overlay`, `kms_draw_boot_splash`, and `kms_draw_log_tail_panel` implementations with `a90_hud_*` calls.
- Kept `screenmenu`, `blindmenu`, app routing, displaytest, cutoutcal, and inputmonitor logic in the v88 include tree.
- Added a small `a90_hud_storage_status` bridge so HUD rendering does not directly depend on the include-tree `boot_storage` static state.
- Updated version/changelog/kmsg markers to `0.8.19 (v88)` / `A90v88`.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v88` | `2897aacfe521eaeffd09cbaef05b0d42f102090f38e886a76d7e16e34e0e48cc` |
| `stage3/ramdisk_v88.cpio` | `0d5875e70078a25a72c7682fcd5a056be9956ae20ee0e2186aca24f686357091` |
| `stage3/boot_linux_v88.img` | `a8b7a79be3866533042d9fbf883587943c12d195eb3486289b15683317852a6a` |

## Validation

- Local build: static ARM64 multi-source build with `-Wall -Wextra` — PASS
- Static checks: no old direct HUD renderer names in v88 include tree — PASS
- Host script checks: `py_compile` for `a90ctl.py`, `native_init_flash.py`, `tcpctl_host.py`, `netservice_reconnect_soak.py` — PASS
- Boot image markers: `A90 Linux init 0.8.19 (v88)`, `A90v88`, `0.8.19 v88 HUD API` — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v88.img --from-native --expect-version "A90 Linux init 0.8.19 (v88)" --verify-protocol auto` — PASS
- Boot partition prefix readback: SHA256 matched `stage3/boot_linux_v88.img` — PASS
- Post-boot cmdv1 verify: `version` and `status` rc=0/status=ok — PASS
- HUD/display/storage regression: `statushud`, `autohud 2`, `watchhud 1 2`, `displaytest safe`, `storage`, `mountsd status` — PASS
- Menu blocking regression: `screenmenu` displayed and raw `q` cancel returned shell control — PASS

## Manual Follow-up

- Optional physical-button pass: use actual VOL+/VOL-/POWER presses in `screenmenu`, `blindmenu`, `waitkey`, `waitgesture`, and `inputmonitor 0`.
- Optional visual pass: confirm boot splash, HUD rows, hidden-menu log tail, and menu log tail are visually unchanged from v87.

## Notes

- Latest verified is now `A90 Linux init 0.8.19 (v88)`.
- v88 intentionally avoids menu/controller extraction. The next split should plan `a90_menu.c/h` boundaries without introducing `hud -> menu` or `input -> menu` dependencies.
