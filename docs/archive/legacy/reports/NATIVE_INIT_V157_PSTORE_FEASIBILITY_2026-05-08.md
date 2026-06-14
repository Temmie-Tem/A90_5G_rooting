# Native Init v157 Pstore/Ramoops Feasibility Report (2026-05-08)

## Result

- status: PASS
- build: `A90 Linux init 0.9.57 (v157)`
- marker: `0.9.57 v157 PSTORE FEASIBILITY`
- boot image: `stage3/boot_linux_v157.img`

## Artifacts

```text
778958c79b6eaad84b0ad4058a20e829e52c9cca8163a2c32056afa995eaa0db  stage3/linux_init/init_v157
08a497eee1af6bcdc23863ecad9bd2820cd0db38d15ed0e0fd332dcbf72b7067  stage3/ramdisk_v157.cpio
8e6c4da691429518ffe7e87f2cc105b38c9b259584ec47f89546a1882c644b72  stage3/boot_linux_v157.img
```

## Implemented

- Added `stage3/linux_init/a90_pstore.c`.
- Added `stage3/linux_init/a90_pstore.h`.
- Added `pstore [summary|full|paths]`.
- Added pstore summary to `status` and `bootstatus`.
- Added `scripts/revalidation/pstore_feas_collect.py`.

## Device Evidence

```text
pstore=fs=yes mounted=no dir=yes entries=0 ramoops_cmdline=no module=yes params=9
```

Detailed evidence:

```text
support: fs_pstore=yes mounted=no dir=yes entries=0
entries: dmesg=0 console=0 ftrace=0 pmsg=0 other=0
cmdline: pstore=no ramoops=no sec_debug_or_sec_log=yes
ramoops: module_dir=yes parameters=9
```

## Validation

```text
native_init_flash.py stage3/boot_linux_v157.img --from-native --expect-version "A90 Linux init 0.9.57 (v157)" --verify-protocol auto
cmdv1 version/status: PASS
pstore: PASS
pstore full: PASS
pstore paths: PASS
pstore_feas_collect.py: PASS failed_commands=0
native_integrated_validate.py: PASS commands=25
git diff --check: PASS
python3 -m py_compile: PASS
```

## Notes

- Kernel supports pstore and exposes `/sys/fs/pstore`, but pstore is not mounted in the current native init state.
- No pstore entries were present during this sample.
- `ramoops` module parameters exist, but kernel cmdline does not expose a direct `ramoops` token.
- Reboot-survival validation remains an explicit opt-in future test.

## Next

- v158: Watchdog Read-only Feasibility.
- v159: Tracefs/Ftrace Feasibility.

