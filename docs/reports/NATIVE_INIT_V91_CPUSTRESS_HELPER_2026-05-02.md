# Native Init v91 CPU Stress Helper Report (2026-05-02)

## Summary

- Build: `A90 Linux init 0.8.22 (v91)`
- Source: `stage3/linux_init/init_v91.c` + `stage3/linux_init/v91/*.inc.c`
- New helper: `stage3/linux_init/helpers/a90_cpustress.c`
- Boot image: `stage3/boot_linux_v91.img`
- Goal: move CPU stress worker forking out of PID1 and validate helper process lifecycle through `a90_run`.

## Changes

- Added static `/bin/a90_cpustress` to the boot ramdisk.
- Replaced PID1 internal CPU stress worker forks in shell `cpustress` with helper execution through `a90_run_wait()`.
- Reworked the menu CPU stress app to track one helper PID instead of an internal worker PID array.
- Added process-group stop support to `a90_run` so q cancel and timeout stop helper worker trees.
- Preserved v90 command syntax, menu duration choices, display/HUD behavior, storage behavior, and shell protocol framing.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v91` | `886f267b26ce4198668f933dafafbe93b81a8aa6c9bbec05cc77958b76aaf65d` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/ramdisk_v91.cpio` | `ebd8c61fbc45c36aaecc77d98c29c54e4beacabd8369cb56b54d90a10668cac1` |
| `stage3/boot_linux_v91.img` | `a0f027375da3bdd92fc2a4f3d6ed1e6a7ff3963dfcc5961d699dcb829477607f` |

## Validation

- Local static ARM64 helper/init build with `-Wall -Wextra` — PASS
- `git diff --check` — PASS
- Host Python `py_compile` — PASS
- `readelf -d` static check for helper/init — PASS
- Boot image markers: `A90 Linux init 0.8.22 (v91)`, `A90v91`, `0.8.22 v91 CPUSTRESS HELPER` — PASS
- Ramdisk contains `/init`, `/bin/a90sleep`, `/bin/a90_cpustress` — PASS
- v91 tree old PID1 `cpustress_worker` and CPU stress PID array management removed — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v91.img --from-native --expect-version "A90 Linux init 0.8.22 (v91)" --verify-protocol auto` — PASS
- Boot partition prefix readback: SHA256 matched `stage3/boot_linux_v91.img` — PASS
- Post-boot `cmdv1 version/status` — PASS
- Helper regression: `run /bin/a90_cpustress 1 1`, `cpustress 3 2`, q cancel with no `a90_cpustress` process left — PASS
- Display/menu regression: `statushud`, `autohud 2`, `watchhud 1 2`, `screenmenu`, `hide`, menu-visible `status`, dangerous-command busy gate — PASS

## Notes

- Latest verified is now `A90 Linux init 0.8.22 (v91)`.
- Local artifact retention is now `v91` latest, `v90` rollback, and `v48` known-good fallback.
- The menu CPU stress app code now uses the helper path, but physical-button start/back verification remains a useful optional manual pass.
- Good next candidates are shell/controller cleanup or storage/netservice policy layering.
