# NATIVE_INIT V2372 — Android route-delta logcat observability

## Scope

V2372 is a host-only runner-observability unit after V2371. V2371 proved the rollbackable Android handoff works, but the raw `app_process` AudioTrack stimulus was killed with rc `137`, no active AudioFlinger track survived into the active snapshot, and mixer deltas stayed at `0`. Repeating the same live route-delta without new observability would be low-information.

This unit changes only the Android route-delta runner and its tests. It does not flash, boot Android, play audio, run native `tinymix set`, open/write `/dev/snd`, run `tinyplay`, or touch Wi-Fi/network state.

## Change

`workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py` now plans and, in future exact-gated live mode, captures an Android logcat window around the stimulus:

- clear selected Android log buffers before the stimulus window,
- start `adb logcat -v threadtime` across `main`, `system`, `crash`, and `events`,
- keep capture running through the active/post snapshot window,
- terminate logcat before rollback and persist:
  - `stimulus-logcat.stdout.txt`,
  - `stimulus-logcat.stderr.txt`.

The logcat commands inherit the same `--adb` and `--serial` targeting as the rest of the Android handoff path, preserving the V2370 wrong-device guard. The existing exact AUD-3D2 approval gate remains unchanged.

## Safety Boundary

This remains a host-only code/readiness iteration. Future live route-delta still requires the exact gate:

```text
AUD-3D2-android-route-delta go: rollbackable Android AudioTrack speaker route-delta capture, checked-helper boot handoff only, low-amplitude framework playback, no native speaker write, rollback to V2321
```

The added logcat capture is observability only. It does not authorize native speaker writes, native mixer changes, PCM playback, or another live Android route-delta run without a fresh exact gate.

## Dry-Run Evidence

Dry-run with the private V2368 DEX reports:

```text
ok=True live_ready=True safety=True
logcat_clear=adb logcat -b main -b system -b crash -b events -c
logcat_capture=adb logcat -v threadtime -b main -b system -b crash -b events
buffers=main,system,crash,events
```

## Validation

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py tests/test_native_audio_android_route_delta_handoff_v2365.py
PYTHONPATH=tests python3 -m unittest tests.test_native_audio_android_route_delta_handoff_v2365 -v
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Focused route-delta tests: `9` passed. Full suite: `1046` tests passed. `git diff --check` passed.

## Decision

```text
android-route-delta-logcat-observability-ready
```

Next live route-delta attempt should use this updated runner so the rc `137` stimulus kill can be classified from Android `main/system/crash/events` logs before considering an APK-style stimulus replacement.
