# NATIVE_INIT V2425 — ACDB thread-set live runner ADB stage hardening

## Scope

- Unit: host-only runner hardening after V2424.
- Device action: none.
- Native replay: none.
- Native speaker write: none.
- Calibration ioctl: none.

## Problem closed

V2424 failed before measurement at `stage-1`:

- `stage-0` remote directory creation succeeded through Android Magisk root.
- The next command, `adb push` of the private observer binary, failed with
  `adb: error: failed to get feature set: no devices/emulators found`.
- Rollback to V2321 succeeded and final selftest was `fail=0`.

The failure is a transient Android ADB stage-transfer stability gap, not an
observer or ACDB result.

## Change

`workspace/public/src/scripts/revalidation/native_audio_acdb_threadset_clone_follow_live_handoff_v2424.py`
now inserts a bounded `adb wait-for-device` before each staging operation whose
ADB subcommand is `push` or `install`.

The dry-run exposes this as `stage_adb_waits`:

- before stage `1`: `adb wait-for-device` before observer binary `adb push`
- before stage `2`: `adb wait-for-device` before controller script `adb push`
- before stage `3`: `adb wait-for-device` before APK `adb install`

The fix deliberately does not change capture semantics:

- same V2423 hybrid thread-set clone-following observer,
- same transient Magisk-root M0 delivery,
- no persistent Magisk module,
- no native calibration ioctl,
- no native speaker write.

## Validation

- `python3 -m py_compile` on the V2424 runner and tests: pass.
- Focused V2424/V2425 tests: 6 pass.
- Materialized dry-run:
  - `ok=true`
  - `future_live_ready=true`
  - `future_live_blockers=[]`
  - `stage_adb_waits=[1,2,3]`
  - `command_safety.ok=true`

## Next unit

Run the exact-gated Android live handoff again with the hardened V2424 runner.
That should be recorded as the next live V-iteration. If staging reaches
`payload-capture-start-background`, interpret outcomes as:

- `ioctl_entries > 0`: payload capture gate solved; proceed to offline decode and native replay design.
- `ioctl_entries = 0` while logcat proves ACDB edge: M0 timing/attach still insufficient; only then design M1 temporary Magisk module packaging of the same hybrid observer.
- staging fails again before helper execution: continue ADB handoff hardening, not M1 escalation.
