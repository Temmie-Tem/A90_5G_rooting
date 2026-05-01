# v91 Plan: CPU Stress External Helper

Date: `2026-05-02`

## Summary

- Target: `A90 Linux init 0.8.22 (v91)` / `0.8.22 v91 CPUSTRESS HELPER`
- Goal: move CPU stress worker forking out of PID1 into a static `/bin/a90_cpustress` helper.
- Keep shell `cpustress [sec] [workers]` and menu CPU stress UX compatible with v90.

## Key Changes

- Copy v90 to `init_v91.c` and `v91/*.inc.c`, then update version, boot marker, ABOUT, and changelog strings.
- Add `stage3/linux_init/helpers/a90_cpustress.c` and include the built helper in the boot ramdisk as `/bin/a90_cpustress`.
- Extend `a90_run_config` with process-group stop support so cancel/timeout terminates helper worker trees.
- Replace v91 PID1 internal CPU stress worker forks with `a90_run` helper spawn/wait/reap/stop calls.
- Keep storage, netservice, shell protocol, display, and menu routing behavior unchanged.

## Test Plan

- Build helper/init as static ARM64 with `-Wall -Wextra`, then verify `file`, `readelf`, `sha256sum`, and marker strings.
- Generate `stage3/ramdisk_v91.cpio` and `stage3/boot_linux_v91.img` from v90 boot image args with only ramdisk changed.
- Confirm v91 tree has no old PID1 `cpustress_worker` or CPU stress PID array management.
- Flash with `native_init_flash.py stage3/boot_linux_v91.img --from-native --expect-version "A90 Linux init 0.8.22 (v91)" --verify-protocol auto`.
- Validate `run /bin/a90_cpustress 1 1`, `cpustress 3 2`, q cancel, `statushud`, `autohud 2`, `watchhud 1 2`, `screenmenu`, `hide`, and menu-visible busy gate.

## Assumptions

- `/bin/a90_cpustress` is the canonical helper path for v91.
- External helper split is structural hardening, not a new user-facing feature.
- v92 can target shell/controller cleanup or storage/netservice policy layering.
