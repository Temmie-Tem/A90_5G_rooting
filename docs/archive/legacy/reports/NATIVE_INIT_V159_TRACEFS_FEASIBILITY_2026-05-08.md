# Native Init v159 Tracefs/Ftrace Feasibility Report (2026-05-08)

## Result

- status: PASS
- build: `A90 Linux init 0.9.59 (v159)`
- marker: `0.9.59 v159 TRACEFS FEASIBILITY`
- boot image: `stage3/boot_linux_v159.img`

## Artifacts

```text
e73bb65f8475b28d6b01c5a4fcaaca33bccd65a1a172ceb1fadffad7c9ed2a71  stage3/linux_init/init_v159
970b1099581251c84757fbb8f87eafc77eca403bfc72daa37ee5e1109124b29c  stage3/ramdisk_v159.cpio
7e7e81a6af774b3b523c993851d64b86484be4c471dbee02edf062b3903c536f  stage3/boot_linux_v159.img
```

## Implemented

- Added `stage3/linux_init/a90_tracefs.c`.
- Added `stage3/linux_init/a90_tracefs.h`.
- Added `tracefs [summary|full|paths]`.
- Added tracefs summary to `status` and `bootstatus`.
- Added `scripts/revalidation/tracefs_feas_collect.py`.

## Device Evidence

```text
tracefs=fs=yes mounted=no dir=yes debugfs=no current=- tracing_on=- tracers=0 events_sample=0 policy=read-only
```

Detailed evidence:

```text
support: fs_tracefs=yes fs_debugfs=yes mount_tracefs=no mount_debugfs=no
paths: sys_tracing=yes debug_tracing=no root=/sys/kernel/tracing
state: current_tracer=- tracing_on=-
available: tracers_readable=no tracer_sample_count=0 events_readable=no event_sample_lines=0
```

## Validation

```text
native_init_flash.py stage3/boot_linux_v159.img --from-native --expect-version "A90 Linux init 0.9.59 (v159)" --verify-protocol auto
cmdv1 version/status: PASS
tracefs: PASS
tracefs full: PASS
tracefs paths: PASS
tracefs_feas_collect.py: PASS failed_commands=0
native_integrated_validate.py: PASS commands=25
git diff --check: PASS
python3 -m py_compile: PASS
```

## Notes

- Kernel reports tracefs/debugfs support, but neither tracefs nor debugfs is mounted in native init.
- `/sys/kernel/tracing` exists, but core ftrace control files are not readable until tracefs is mounted.
- Mounting tracefs and enabling tracing are intentionally deferred until after baseline/long-soak safety decisions.

## Next

- v160: NCM/TCP Stability before Wi-Fi work.
- v161+: Storage/process/thermal stability cycle before Wi-Fi baseline refresh.
