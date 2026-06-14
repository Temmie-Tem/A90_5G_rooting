# NATIVE_INIT V2373 — Android route stimulus APK fallback

## Scope

V2373 is a host-only fallback-artifact unit after V2371/V2372. V2371 showed that raw `app_process` AudioTrack stimulus was killed with rc `137`. V2372 added Android `logcat` observability for the next exact-gated route-delta run. V2373 prepares the alternate APK-style stimulus path in case the logcat-confirmed cause is raw `app_process` policy/process lifetime.

This unit does not install or run an APK, flash a boot image, boot Android, play audio, run native `tinymix set`, open/write `/dev/snd`, run `tinyplay`, or touch Wi-Fi/network state.

## Added Artifact Source

Public, reproducible source was added under:

```text
workspace/public/src/android/audio_route_stimulus_apk/
```

The APK-style stimulus uses an exported Activity:

```text
package:  com.a90.nativeinit.audio
activity: com.a90.nativeinit.audio.A90AudioRouteStimulusActivity
action:   com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS
```

Behavior:

- uses Android framework `AudioTrack` with `USAGE_MEDIA`, stereo PCM16, default `48000` Hz,
- default duration is `2000` ms and default amplitude is `0.05`,
- accepts intent extras for `duration_ms`, `sample_rate`, `amplitude`, and `speaker`,
- logs `A90_AUDIO_STIMULUS_BEGIN`, `A90_AUDIO_STIMULUS_END`, and error/finish markers for future V2372 logcat capture,
- uses Android framework `AudioManager.setSpeakerphoneOn(true)` only when the speaker hint is enabled,
- does not reference native `/dev/snd`, `tinyplay`, or `tinymix set`.

## Builder

New host-only builder:

```text
workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_apk_v2373.py
```

It uses the existing private V2368 Android/JDK toolchain and writes outputs only under `workspace/private/`:

```text
workspace/private/builds/audio/v2373-android-route-stimulus-apk/
```

The builder performs a no-Gradle Android APK build using `javac`, `d8`, `aapt`, `zipalign`, and `apksigner`, generating a private debug keystore under `workspace/private/inputs/android-debug/` if needed. No generated APK, keystore, class file, dex file, or build log is tracked.

## Private Build Result

The host build completed and verified the signed APK:

```text
built=True
apk=workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk
apk_sha256=d5543153b497087c7145d25c81bd8c874e23e380a1e5af4358f8dda0257b08af
apk_mode=0o600
apk_size=12691
file: Android package (APK), with AndroidManifest.xml, with APK Signing Block
apksigner: Verified using v2 scheme=true, v3 scheme=true, signers=1
```

Future launch shape after a separately gated Android handoff and runner integration:

```text
am start -W -n com.a90.nativeinit.audio/.A90AudioRouteStimulusActivity \
  -a com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS \
  --ei duration_ms 2000 --ei sample_rate 48000 --ef amplitude 0.05 --ez speaker true
```

This command is documented only as the intended Android framework launch path. It was not executed in V2373.

## Safety Boundary

V2373 does not authorize another route-delta live run. Future Android playback still requires the exact AUD-3D2 phrase, checked-helper Android boot handoff, low-amplitude framework playback only, and rollback to V2321. Native speaker writes, native mixer changes, PCM playback, and `tinyplay` remain blocked until a real Android route delta exists.

## Validation

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_apk_v2373.py tests/test_build_android_audio_route_stimulus_apk_v2373.py
PYTHONPATH=tests python3 -m unittest tests.test_build_android_audio_route_stimulus_apk_v2373 -v
python3 workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_apk_v2373.py --dry-run
python3 workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_apk_v2373.py
file workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk
```

Focused V2373 tests: `3` passed. Full suite: `1049` tests passed. `git diff --check` passed.

## Decision

```text
android-route-delta-apk-stimulus-artifact-ready
```

Next safe unit without live playback is runner support for an optional APK mode: stage/install the V2373 APK, launch it with `am start`, collect V2372 logcat markers, and keep the existing exact AUD-3D2 live gate. A live Android route-delta run remains parked until a fresh exact gate is provided.
