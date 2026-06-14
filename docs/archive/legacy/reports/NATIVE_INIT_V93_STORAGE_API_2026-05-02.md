# Native Init v93 Storage API Report (2026-05-02)

## Summary

- Build: `A90 Linux init 0.8.24 (v93)`
- Source: `stage3/linux_init/init_v93.c` + `stage3/linux_init/v93/*.inc.c`
- New module: `stage3/linux_init/a90_storage.c/h`
- Boot image: `stage3/boot_linux_v93.img`
- Goal: make boot storage state, SD probe, cache fallback, and `storage`/`mountsd` command logic explicit without changing storage UX.
- Status: local build, flash, and storage/UI/netservice regression validation complete.

## Changes

- Added `a90_storage.c/h` for cache mount, SD block/UUID/mount/workspace/RW probe, boot storage state, fallback policy, and `storage`/`mountsd` command handlers.
- Replaced include-tree `boot_storage`/`cache_mount_ready` ownership with a compiled storage module and status snapshot API.
- Added boot-progress hooks so storage probing can still update boot splash lines without depending on HUD/menu/shell dispatch.
- Updated HUD storage status, `status`, `storage`, and `mountsd` call sites to use `a90_storage_*` APIs.
- Kept Android layout/run/adbd, netservice, USB gadget policy, and reboot/recovery/poweroff behavior in the include tree for v94+.
- Fixed `mountsd ro/off/init` regression so remounting SD rw/init restores the native log path to `/mnt/sdext/a90/logs/native-init.log`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v93` | `1f013323161b90f1b308631e91a2bbd15fac20d1a86ee3c6990d3c1b1c92855c` |
| `stage3/ramdisk_v93.cpio` | `6a176f9cdf16b98c6945e87f19d754ab8a7e0de5732b2f1b67c52200a3c068e6` |
| `stage3/boot_linux_v93.img` | `d62e861dfec7826a85e37d5f80d9c3ac562e65aaf35f37400d1bdafd5ffc889d` |

## Validation

- Local static ARM64 init build with `-Wall -Wextra` — PASS
- `git diff --check` — PASS
- Host Python `py_compile` — PASS
- `readelf -d` static check for init — PASS
- Boot image markers: `A90 Linux init 0.8.24 (v93)`, `A90v93`, `0.8.24 v93 STORAGE API` — PASS
- Ramdisk contains `/init`, `/bin/a90sleep`, `/bin/a90_cpustress` — PASS
- v93 tree old storage globals removed: `struct boot_storage_state`, `boot_storage.`, `cache_mount_ready`, include-tree `mount_cache()` — PASS
- v93 dispatch/HUD/status call storage through `a90_storage_*` APIs — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v93.img --from-native --expect-version "A90 Linux init 0.8.24 (v93)" --verify-protocol auto` — PASS
- Boot partition prefix readback: SHA256 matched `stage3/boot_linux_v93.img` — PASS
- Post-boot `cmdv1 version/status` — PASS
- Storage regression: `bootstatus`, `logpath`, `timeline`, `storage`, `mountsd status` — PASS
- Remount regression: `mountsd ro`, `mountsd rw`, `mountsd init`, `mountsd off`, `mountsd init`, `mountsd status` — PASS
- Log path recovery: after `mountsd off` + `mountsd init`, `logpath` returned `/mnt/sdext/a90/logs/native-init.log` — PASS
- UI regression: `statushud`, `autohud 2`, nonblocking `screenmenu`, `hide` — PASS
- Network regression: `netservice status` retained v92 behavior with helpers present and disabled flag state — PASS

## Notes

- Latest verified is now `A90 Linux init 0.8.24 (v93)`.
- Local artifact retention is now `v93` latest, `v92` rollback, and `v48` known-good fallback.
- v94 primary candidate: `a90_netservice.c/h` and possibly `a90_usb_gadget.c/h` for NCM/tcpctl/USB configfs policy.
