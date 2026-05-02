# Native Init v94 Boot Selftest API Report (2026-05-03)

## Summary

- Build: `A90 Linux init 0.8.25 (v94)`
- Source: `stage3/linux_init/init_v94.c` + `stage3/linux_init/v94/*.inc.c`
- New module: `stage3/linux_init/a90_selftest.c/h`
- Boot image: `stage3/boot_linux_v94.img`
- Goal: run a fast non-destructive boot selftest and expose the result through boot splash, log, timeline, `status`, `bootstatus`, and `selftest`.
- Status: local build, flash, and selftest/storage/UI/netservice regression validation complete.

## Changes

- Added `a90_selftest.c/h` with `PASS`/`WARN`/`FAIL` entries, last-run summary, entry accessors, and boot hook callbacks.
- Runs boot selftest after ACM gadget setup and before `/dev/ttyGS0` wait; failures remain warn-only and do not block shell/HUD entry.
- Checks log readiness, timeline, storage status, metrics snapshot, KMS framebuffer, input event nodes, service registry, and ACM configfs state.
- Added `selftest [status|run|verbose]` shell command and included selftest summary in `status` and `bootstatus`.
- Kept destructive operations out of selftest: no USB rebind, NCM start/stop, mount mode changes, cpustress, reboot, recovery, or partition writes.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v94` | `c679e021a154643d1b84dfe955c56591cf4fc113d1cd5d6aea8b6c8581aa64bd` |
| `stage3/ramdisk_v94.cpio` | `31a69d6463131587e48462e05a61c15966f7dc20daf7d0a1099117041164b6be` |
| `stage3/boot_linux_v94.img` | `ecf0665bc47c9315edaeb46b38ffe0c64c4ff6b6498378292934d8c580753d98` |

## Validation

- Local static ARM64 init build with `-Wall -Wextra` — PASS
- `git diff --check` — PASS
- Host Python `py_compile` — PASS
- Boot image markers: `A90 Linux init 0.8.25 (v94)`, `A90v94`, `0.8.25 v94 BOOT SELFTEST API` — PASS
- Ramdisk contains `/init`, `/bin/a90sleep`, `/bin/a90_cpustress` — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v94.img --from-native --expect-version "A90 Linux init 0.8.25 (v94)" --verify-protocol auto` — PASS
- Boot partition prefix readback: SHA256 matched `stage3/boot_linux_v94.img` — PASS
- Post-boot `cmdv1 version/status` — PASS
- Boot selftest: `pass=8 warn=0 fail=0 duration=39ms` on verified boot — PASS
- Manual selftest: `selftest`, `selftest verbose`, `selftest run` — PASS
- Timeline/log validation: `timeline` includes `selftest`, `logcat` contains selftest item results — PASS
- Storage regression: `storage`, `mountsd status`, `logpath` — PASS
- UI regression: `statushud`, `autohud 2`, nonblocking `screenmenu`, `hide` — PASS
- Network regression: `netservice status` retained disabled/default behavior with helpers present — PASS

## Notes

- Latest verified is now `A90 Linux init 0.8.25 (v94)`.
- Local artifact retention is now `v94` latest, `v93` rollback, and `v48` known-good fallback.
- v95 primary candidate: `a90_usb_gadget.c/h` + `a90_netservice.c/h` for USB configfs/NCM/tcpctl policy separation.
