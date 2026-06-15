# NATIVE_INIT_V2479_AUDIO_ACDBTAP_LINKER_NAMESPACE_BLOCK_2026-06-15

## Decision

`v2479-acdbtap-linker-namespace-block`

The corrected V2477 live capture was executed with `--run-live --from-native`
after the V2478 staging permission fix. Android handoff, Magisk root settle,
`libacdbtap.so` staging, and cleanup/rollback all worked, but the preload did
not enter `android.hardware.audio.service`. The runner stopped before playback,
as designed.

## Live run

Private run directory:

- `workspace/private/runs/audio/v2477-acdbtap-live-handoff-20260615-224405/`

High-level result:

- decision: `v2477-acdbtap-live-handoff-preload-not-confirmed-before-rollback-rollback-pass`
- Android flash/handoff: passed
- Magisk root settle: passed
- stage setup: passed
- `adb push` into `incoming/`: passed after V2478
- root install of `libacdbtap.so`: passed
- manual HAL preload confirmation: failed
- playback: **not run**
- ACDB tap events: none
- rollback to V2321: passed, final native `selftest fail=0`

## Evidence

The staged library was installed at:

```text
/data/local/tmp/a90-acdbtap-v2476/lib/libacdbtap.so
```

The file existed and was readable:

```text
-rw-r--r-- 1 root root u:object_r:shell_data_file:s0 5864 ... libacdbtap.so
```

The manual re-exec attempted to run the HAL with `LD_PRELOAD`, but the new
process failed at the dynamic linker before it could appear in `/proc/<pid>/maps`:

```text
linker: library "/data/local/tmp/a90-acdbtap-v2476/lib/libacdbtap.so" ...
is not accessible for the namespace: [name="(default)",
ld_library_paths="", default_library_paths="/vendor/lib:/vendor/lib/hw:/vendor/lib/egl",
permitted_paths="/odm:/vendor:/system/vendor"]

linker: CANNOT LINK EXECUTABLE "/vendor/bin/hw/android.hardware.audio.service":
library "/data/local/tmp/a90-acdbtap-v2476/lib/libacdbtap.so" ... is not accessible
for the namespace "(default)"
```

`setprop ctl.stop vendor.audio-hal` did stop the init-managed HAL, but init
restarted the stock service immediately after the manual exec failed. The live
runner saw only the stock HAL PID in `pidof android.hardware.audio.service` and
therefore did not run the AudioTrack stimulus.

Relevant kernel/init lines confirmed the control path:

```text
init: Sending signal 9 to service 'vendor.audio-hal' ...
init: Control message: Processed ctl.stop for 'vendor.audio-hal'
init: Service 'vendor.audio-hal' ... received signal 9
init: starting service 'vendor.audio-hal'...
```

## Classification

This is `preload-not-confirmed`, not `captured-acdbtap-full-outbuf-set-no-4916`.
No ACDB `out_len>0` rows were captured, because playback was intentionally
aborted before stimulus.

The blocker is not the V2478 `adb push` staging path and not a native replay
issue. It is the Android dynamic linker namespace: a vendor HAL cannot preload a
library from `/data/local/tmp` because that path is outside the vendor namespace
permitted paths.

## Boundary

No native calibration ioctl ran. No native mixer write ran. No AudioTrack
stimulus ran. No SELinux policy change or `setenforce 0` was attempted. The
only persistent partition write was the checked boot handoff/rollback path, and
rollback to V2321 completed with `selftest fail=0`.

## Next

The next viable design is a bounded temporary Magisk/systemless measurement
capsule that makes the same 32-bit `libacdbtap.so` visible under a vendor
namespace-accessible path, e.g. `/vendor/lib/libacdbtap.so`, then uses
`LD_PRELOAD=/vendor/lib/libacdbtap.so` for the manual HAL exec.

That follow-on must keep the same constraints:

- temporary Magisk/module state only, cleaned before rollback;
- no destructive `/data` action;
- no native calibration ioctl;
- no playback unless `/proc/<pid>/maps` confirms `libacdbtap` in the HAL;
- if the result becomes `captured-acdbtap-full-outbuf-set-no-4916`, preserve it
  as a partial success because the per-device AFE / ASM / ADM / VOL payload set
  is still operator-valuable.
