# Native Init v158 Watchdog Read-only Feasibility Report (2026-05-08)

## Result

- status: PASS
- build: `A90 Linux init 0.9.58 (v158)`
- marker: `0.9.58 v158 WATCHDOG FEASIBILITY`
- boot image: `stage3/boot_linux_v158.img`

## Artifacts

```text
d131066a794a63f572df6c9739f8f323447dc8f8639a91f987b76302f03bd298  stage3/linux_init/init_v158
037f708dda0d074cef620aa7c56252ed50a00e422d36b3d9e541d6c5df4816d8  stage3/ramdisk_v158.cpio
944e6806c5a558560308055b1268d80054878802326f039921ee5c4f178bc396  stage3/boot_linux_v158.img
```

## Implemented

- Added `stage3/linux_init/a90_watchdoginv.c`.
- Added `stage3/linux_init/a90_watchdoginv.h`.
- Added `watchdoginv [summary|full|paths]`.
- Added watchdog summary to `status` and `bootstatus`.
- Added `scripts/revalidation/watchdog_feas_collect.py`.

## Device Evidence

```text
watchdoginv=class=1 dev=no dev0=no attrs=0 armed_hints=0 policy=read-only-no-open
```

Detailed evidence:

```text
summary: class_dir=yes class=1 dev_watchdog=no dev_watchdog0=no attrs=0 armed_hints=0
cmdline: watchdog=no nowayout=no
watchdog0:
```

## Validation

```text
native_init_flash.py stage3/boot_linux_v158.img --from-native --expect-version "A90 Linux init 0.9.58 (v158)" --verify-protocol auto
cmdv1 version/status: PASS
watchdoginv: PASS
watchdoginv full: PASS
watchdoginv paths: PASS
watchdog_feas_collect.py: PASS failed_commands=0
native_integrated_validate.py: PASS commands=25
git diff --check: PASS
python3 -m py_compile: PASS
```

## Notes

- `/sys/class/watchdog/watchdog0` exists, but `/dev/watchdog` and `/dev/watchdog0` are absent in the current native init state.
- No readable watchdog attributes were exposed by the current sysfs node.
- v158 intentionally does not open watchdog character devices, so there is no watchdog arm/ping/reboot risk.

## Next

- v159: Tracefs/Ftrace Feasibility.

