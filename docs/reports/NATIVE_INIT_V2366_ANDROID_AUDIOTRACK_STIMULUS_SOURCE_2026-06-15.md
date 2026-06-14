# NATIVE_INIT V2366 — Android AudioTrack stimulus source

Date: 2026-06-15

## Scope

- Unit: host-only source and builder staging for the missing V2365 `A90AudioRouteStimulus.dex`.
- Touched public code:
  - `workspace/public/src/android/audio_route_stimulus/A90AudioRouteStimulus.java`
  - `workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_v2366.py`
  - `tests/test_build_android_audio_route_stimulus_v2366.py`
- No DEX was built.
- No Android boot, device command, playback, mixer write, or flash ran.

## Result

Decision: `v2366-audiotrack-stimulus-source-ready-toolchain-missing`.

The project now has the Java source for the route-delta playback stimulus plus a private-output
builder. The source uses Android framework `AudioTrack`, `USAGE_MEDIA`, stereo `PCM_16BIT`, default
48 kHz, 2 seconds, and amplitude `0.05`. It prints begin/end markers and exits after one bounded
run.

The DEX is still not built because this host currently lacks the required Java/Android toolchain:
`javac`, `d8` or `dx`, and an Android platform `android.jar`.

## Builder behavior

`build_android_audio_route_stimulus_v2366.py`:

- discovers `javac`,
- discovers `d8` or `dx`,
- discovers `android.jar` via `--android-jar`, `--android-home`, `ANDROID_HOME`, or
  `ANDROID_SDK_ROOT`,
- compiles `A90AudioRouteStimulus.java`,
- emits `workspace/private/builds/audio/v2366-android-route-stimulus/A90AudioRouteStimulus.dex`,
- chmods the DEX to `0600`,
- writes a private manifest with SHA256 and size.

In the current environment, dry-run correctly reports the missing toolchain instead of creating a
fake artifact.

## Safety boundary

- No `tinyplay`.
- No native `/dev/snd`.
- No native `tinymix set`.
- No device command.
- No generated binary committed.
- Future live route-delta remains blocked until a real DEX is built under `workspace/private/` and
  V2365 `--stimulus-dex` reports `live_ready=true`.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_v2366.py tests/test_build_android_audio_route_stimulus_v2366.py`
- `PYTHONPATH=tests python3 -m unittest tests.test_build_android_audio_route_stimulus_v2366 -v`
- `python3 workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_v2366.py --dry-run`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `git diff --check`
