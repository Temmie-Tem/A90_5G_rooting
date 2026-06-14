# NATIVE_INIT V2374 — Android route-delta APK-mode runner integration

## Scope

V2374 is a host-only runner-integration unit after V2371/V2372/V2373.

V2371 proved the rollbackable Android handoff path but the raw `app_process` AudioTrack stimulus died with rc `137`, leaving no active AudioFlinger track and `0` mixer deltas. V2372 added Android `logcat` capture around the stimulus window. V2373 built and verified a private APK-style AudioTrack stimulus, but did not wire it into the live route-delta runner.

This unit integrates that private APK into the existing route-delta runner command graph. It does not flash, boot Android, install the APK on a device, play audio, run native `tinymix set`, open/write `/dev/snd`, run `tinyplay`, or touch Wi-Fi/network state.

## Change

`workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py` now accepts:

```text
--stimulus-mode dex|apk
--stimulus-apk <private APK path>
```

The original DEX/app_process path remains the default. APK mode changes only the Android framework stimulus delivery path:

| Phase | APK-mode command shape |
| --- | --- |
| Stage | `adb install -r <A90AudioRouteStimulus.apk>` |
| Playback | `adb shell su -c 'am start -W -n com.a90.nativeinit.audio/.A90AudioRouteStimulusActivity -a com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS ...'` |
| Result check | `pidof com.a90.nativeinit.audio`, `cmd package path com.a90.nativeinit.audio` |
| Cleanup | `adb uninstall com.a90.nativeinit.audio` plus remote temp-dir removal |

The APK path is validated as private input before live readiness:

- file exists,
- size is non-zero,
- not group/world writable,
- starts with ZIP/APK magic `PK\x03\x04`.

The V2370 wrong-device guard is preserved: `--adb` and `--serial` propagate to APK install, playback, result, and uninstall commands.

## Private APK Dry-Run Evidence

Dry-run against the V2373 private APK:

```text
ok=True
live_ready=True
command_safety.ok=True
stimulus_mode=apk
stimulus_apk.ok=True
stimulus_apk.sha256=d5543153b497087c7145d25c81bd8c874e23e380a1e5af4358f8dda0257b08af
stage_last=adb install -r workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk
playback_start_background=adb shell su -c 'am start -W -n com.a90.nativeinit.audio/.A90AudioRouteStimulusActivity -a com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS --ei duration_ms 2000 --ei sample_rate 48000 --ef amplitude 0.05 --ez speaker true'
cleanup_last=adb uninstall com.a90.nativeinit.audio
live_blockers=[]
```

## Magisk Module Direction

The historical Wi-Fi/Android handoff work used Magisk modules when the measurement needed early Android boot timing or a systemless vendor overlay, e.g. wrapper-based `mdm_helper` syscall capture. That pattern is valid but heavier:

```text
native -> Android boot -> install module -> second Android boot for module effect -> capture -> remove module -> rollback native
```

For this route-delta frontier, the lower-risk order is:

1. Use APK mode first, because it is a normal Android framework app launch and does not require a persistent Magisk module or second Android boot.
2. If APK install/launch is blocked by Android policy, process lifetime, or package privileges, design a Magisk-module delivery unit as a follow-on. The likely use would be systemless installation of a small privileged/system app or boot-time service that starts the same low-amplitude framework AudioTrack stimulus.
3. Keep Magisk module work separate from V2374 and from native speaker writes. It must remain rollbackable, remove the module before returning to native, and avoid direct vendor/system partition writes.

## Safety Boundary

The script still retains the exact AUD-3D2 phrase as an internal live-run safety latch. `GOAL.md` now pre-authorizes recoverable boot-partition-only audio device steps, so the loop should not stop merely to ask for human approval; however, this host-only V2374 unit does not run live and intentionally leaves the runner's exact phrase gate unchanged.

Native speaker writes, native mixer changes, PCM playback open/write, and `tinyplay` remain blocked until Android route-delta evidence identifies a speaker route.

## Validation

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py tests/test_native_audio_android_route_delta_handoff_v2365.py
PYTHONPATH=tests python3 -m unittest tests.test_native_audio_android_route_delta_handoff_v2365 -v
python3 workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py --dry-run --stimulus-mode apk --stimulus-apk workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Results:

```text
focused route-delta tests: 11 passed
APK-mode dry-run: ok=True live_ready=True command_safety.ok=True
full unittest discovery: 1051 passed
git diff --check: passed
```

## Decision

```text
android-route-delta-apk-mode-runner-ready
```

Next unit should use the pre-authorized Android route-delta live path with APK mode plus V2372 logcat capture, checked-helper Android handoff, bounded low-amplitude framework playback, and rollback to V2321. If APK mode still fails to produce an AudioFlinger-active window, classify with logcat first; only then consider a Magisk-module delivery design.
