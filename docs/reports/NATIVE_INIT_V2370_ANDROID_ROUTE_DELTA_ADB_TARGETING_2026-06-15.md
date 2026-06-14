# NATIVE_INIT_V2370_ANDROID_ROUTE_DELTA_ADB_TARGETING_2026-06-15

## Scope

V2370 is a host-only safety/readiness unit for the Android route-delta runner. No device action ran: no flash, no Android boot, no playback, no `tinymix set`, no native `/dev/snd` open/write, no `tinyplay`, and no Wi-Fi/network action.

The reason for this unit is concrete: V2369 made the runner live-capable, but most ADB stage/snapshot/rollback commands still implicitly targeted the default `adb` device. In a multi-device or stale-ADB environment that is a wrong-device risk. V2370 makes the ADB target explicit and test-covered before any live run.

## Changes

- Adds `--adb` and `--serial` to `native_audio_android_route_delta_handoff_v2365.py`.
- Propagates the same ADB target into:
  - `native_init_flash.py` Android handoff command via `--adb` and optional `--serial`.
  - all `adb shell su -c ...` stage/snapshot/playback/cleanup commands.
  - all `adb push` staging commands.
  - Android `adb reboot recovery` before rollback.
  - V2321 rollback helper invocation via `--adb` and optional `--serial`.
- Keeps exact AUD-3D2 approval gating unchanged.
- Keeps dry-run as default and leaves live route-delta capture parked.

## Dry-run Check

With a custom ADB executable and serial, the dry-run command graph now carries the selected target through flash, stage, snapshots, recovery reboot, and rollback. The focused regression test `test_adb_target_is_propagated_to_flash_stage_snapshot_and_rollback` covers this contract.

## Validation

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py tests/test_native_audio_android_route_delta_handoff_v2365.py
PYTHONPATH=tests python3 -m unittest tests.test_native_audio_android_route_delta_handoff_v2365 -v
```

Focused route-delta tests: 8 passed.

Full unittest discovery and `git diff --check` are recorded in the commit output for this unit.

## Gate Status

Android route-delta live capture is still not executed. It still requires the exact full AUD-3D2 phrase:

```text
AUD-3D2-android-route-delta go: rollbackable Android AudioTrack speaker route-delta capture, checked-helper boot handoff only, low-amplitude framework playback, no native speaker write, rollback to V2321
```
