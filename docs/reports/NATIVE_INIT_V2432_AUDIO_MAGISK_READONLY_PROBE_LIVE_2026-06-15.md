# NATIVE_INIT V2432 — Audio Magisk Read-Only Access Probe Live

Date: 2026-06-15

## Purpose

Classify the V2430 failure that blocked the temporary Magisk M1 module path before
activation. V2430 attempted direct placement under `/data/adb/modules/...` and failed
at staging. V2432 is a read-only Android/Magisk access probe only:

- boot the pinned Android image through the checked helper,
- confirm Magisk root availability,
- inspect Magisk paths and `/data/adb` visibility from shell, `su -c`, and `su -mm -c`,
- perform no writes under `/data/adb`, no module install/remove, no playback, no mixer/PCM,
  and no calibration ioctl,
- roll back to V2321 and verify native health.

Exact live gate used:

```text
AUD-5H-magisk-readonly-probe go: rollbackable Android Magisk access probe, read-only /data/adb namespace inspection only, no module install, no playback, rollback to V2321
```

## Implementation

Added the exact-gated runner:

- `workspace/public/src/scripts/revalidation/native_audio_magisk_readonly_probe_live_handoff_v2432.py`
- `tests/test_native_audio_magisk_readonly_probe_live_handoff_v2432.py`

The runner performs the Android handoff and rollback using the checked flash helper and runs
only read-only probe commands. During pre-commit review an initial private run exposed an
`adb shell su -c` quoting bug: the multi-line probe was not passed as the `-c` argument,
so Magisk printed a usage error and the script body ran as `shell`. The runner was fixed to
send a single remote-shell command string (`su -c '<script>'` / `su -mm -c '<script>'`), and
the summarizer now requires `uid=0(root)` and rejects MagiskSU usage errors.

## Validation

Host/static validation:

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_magisk_readonly_probe_live_handoff_v2432.py tests/test_native_audio_magisk_readonly_probe_live_handoff_v2432.py
PYTHONPATH=tests python3 -m unittest tests/test_native_audio_magisk_readonly_probe_live_handoff_v2432.py
PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_magisk_readonly_probe_live_handoff_v2432.py --dry-run
```

Focused tests passed after the quoting fix. The dry-run reports `future_live_ready=true` and
`command_safety.ok=true`; forbidden token checks include Magisk install/remove, module write
operations, playback, calibration ioctl, fastboot, and raw partition write.

Pre-live rollback and current-native safety checks:

- V2321 rollback image SHA256 matched:
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- V2237 fallback SHA256 matched:
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- V48 fallback exists and SHA256 recorded locally.
- Pre-live native `selftest verbose`: `fail=0`.

## Live Result

Private run directory:

```text
workspace/private/runs/audio/v2432-magisk-readonly-probe-20260615-130827
```

Result decision after corrected classifier:

```text
v2432-magisk-readonly-probe-mount-master-readonly-visible-no-denial-before-rollback-rollback-pass
```

Key results:

- Android boot image sealed to a run-local `0600` copy and flashed with expected SHA256
  `c15ce425abb8da41f0b1696d19d05a625fd7cec949b4ae50651a5f1e7293057b`.
- Android boot-complete and Magisk root settle passed; `su -c id` returned `uid=0(root)`.
- `probe-shell-readonly` remained shell and saw `Permission denied` for `/data/adb*`, as expected.
- `probe-su-readonly` executed as `uid=0(root)` / `u:r:magisk:s0` and read `/data/adb`,
  `/data/adb/modules`, and `/data/adb/service.d` with no permission-denied lines.
- `probe-su-mount-master-readonly` also executed as `uid=0(root)` / `u:r:magisk:s0` and read the
  same paths with no permission-denied lines.
- `/data/adb/modules_update` did not exist in this Android boot; that is not a permission denial.
- No `/data/adb` writes, module installation/removal, playback, mixer/PCM action, or
  calibration ioctl was executed.
- Rollback to V2321 completed through the checked helper.
- Post-rollback native `selftest verbose`: `fail=0`.

Representative root probe evidence:

```text
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
/system_ext/bin/magisk
30.7:MAGISK:R (30700)
/debug_ramdisk
drwx------  6 root root u:object_r:adb_data_file:s0 /data/adb
drwxr-xr-x  2 root root u:object_r:system_file:s0   /data/adb/modules
drwxr-xr-x  2 root root u:object_r:adb_data_file:s0 /data/adb/service.d
```

## Conclusion

V2432 re-opens the Magisk module direction as a valid Android-good measurement mechanism.
The decisive correction is that V2430's direct staging failure is now suspect as a command
construction/quoting problem, not proof that `/data/adb/modules` is inaccessible to Magisk root.
With the corrected `adb shell "su -c '<script>'"` style, both normal Magisk root and
mount-master root can read the module namespace.

The module path remains measurement-only:

- not a native-init runtime dependency,
- not a native audio replay path,
- not a calibration ioctl or speaker playback path,
- only a rollbackable Android-side capture capsule, similar to the earlier Wi-Fi handoff style.

Next safe unit:

1. **V2433 host-only design** for a bounded Magisk module staging cleanup probe using corrected
   `su -c` quoting. It should create and remove a unique inert test directory only after exact
   gating, prove targeted cleanup, and leave no residue.
2. If V2433 passes, retry M1 temporary module activation with the same corrected quoting.
3. Keep `magisk --install-module` deferred unless direct targeted staging/cleanup fails; the
   installer path is broader and cleanup semantics are less targeted.

Do not jump straight to module activation or native ACDB replay from this report alone.
