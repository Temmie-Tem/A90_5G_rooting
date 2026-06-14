# NATIVE_INIT V2368 — Android AudioTrack stimulus DEX build

Date: 2026-06-15

## Scope

- Unit: host-only toolchain bootstrap and DEX build for the V2362 Android route-delta capture path.
- Device action: none.
- Flash action: none.
- Audio action: none.
- Private outputs only: JDK/SDK downloads, installed SDK packages, and the generated DEX remain under `workspace/private/` and are not committed.

## Source basis

- Android documents the command-line tools as the `cmdline-tools` package under `android_sdk/cmdline-tools/version/bin/` and says the package can be downloaded without Android Studio: https://developer.android.com/tools
- Android documents `sdkmanager` as the tool for installing SDK packages and shows installing package names such as `build-tools;36.0.0` and `platforms;android-36`: https://developer.android.com/tools/sdkmanager
- Android command-line tools release notes document the command-line tools package as the current replacement for the deprecated SDK Tools package: https://developer.android.com/tools/releases/cmdline-tools
- Eclipse Adoptium documents Temurin JDK releases and the REST/GitHub distribution channels: https://adoptium.net/temurin/releases/?version=17

## Implementation

Added `workspace/public/src/scripts/revalidation/bootstrap_android_audio_stimulus_toolchain_v2368.py`.

The helper stages a private toolchain:

- Temurin JDK 17.0.19+10 archive:
  - URL: `https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.19%2B10/OpenJDK17U-jdk_x64_linux_hotspot_17.0.19_10.tar.gz`
  - private path: `workspace/private/inputs/downloads/v2368-android-audio-toolchain/OpenJDK17U-jdk_x64_linux_hotspot_17.0.19_10.tar.gz`
  - SHA256: `d8afc263758141a66e0e3aafc321e783f7016696f4eaea067d340a269037d331`
  - size: `193335385`
  - extracted JDK: `workspace/private/inputs/toolchains/temurin17-v2368/jdk-17.0.19+10`
  - `javac -version`: `javac 17.0.19`
- Android command-line tools archive:
  - URL: `https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip`
  - private path: `workspace/private/inputs/downloads/v2368-android-audio-toolchain/commandlinetools-linux-13114758_latest.zip`
  - SHA256: `7ec965280a073311c339e571cd5de778b9975026cfcbe79f2b1cdcb1e15317ee`
  - size: `164760899`
  - installed layout: `workspace/private/inputs/android-sdk-v2368/cmdline-tools/latest`
- Installed Android SDK packages:
  - `platforms;android-31`
  - `build-tools;35.0.0`
  - `android.jar`: `workspace/private/inputs/android-sdk-v2368/platforms/android-31/android.jar`
  - `d8`: `workspace/private/inputs/android-sdk-v2368/build-tools/35.0.0/d8`
  - `d8 --version`: `D8 8.6.2-dev (build abaab469b5ebd4dd2bb91ba0ed6f45277faae4ca from go/r8bot (luci-r8-custom-ci-archive-0-77gl))`

The helper also fixes the command-line tools archive extraction mode issue by explicitly marking tools under `cmdline-tools/latest/bin/` executable. The first attempted install exposed this as `PermissionError: [Errno 13] Permission denied: .../sdkmanager`; the retry passed after the fix.

Updated `workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_v2366.py` to accept `--java-home` and inject that private JDK into `PATH`/`JAVA_HOME` for both `javac` and the `d8` shell wrapper. Without this, `d8` failed with `exec: java: not found` on this host.

## DEX result

Built the Android framework stimulus from `workspace/public/src/android/audio_route_stimulus/A90AudioRouteStimulus.java`:

- DEX: `workspace/private/builds/audio/v2366-android-route-stimulus/A90AudioRouteStimulus.dex`
- file type: `Dalvik dex file version 035`
- SHA256: `95c27a152acee5c57d634e03436f72166999f5fd809d772f8f6414a3f9dc2b57`
- size: `4264`
- mode: `0600`

Command shape:

```bash
python3 workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_v2366.py \
  --java-home workspace/private/inputs/toolchains/temurin17-v2368/jdk-17.0.19+10 \
  --android-home workspace/private/inputs/android-sdk-v2368 \
  --android-jar workspace/private/inputs/android-sdk-v2368/platforms/android-31/android.jar \
  --d8 workspace/private/inputs/android-sdk-v2368/build-tools/35.0.0/d8
```

`javac` emitted the expected warning `bootstrap class path not set in conjunction with -source 8`; the DEX still built successfully and passed the DEX magic/file checks.

## Route-delta readiness

`native_audio_android_route_delta_handoff_v2365.py --dry-run --stimulus-dex <DEX>` now reports:

- decision: `v2365-android-route-delta-runner-dry-run`
- `ok=True`
- `live_ready=True`

This closes the V2366 DEX artifact gap. It does **not** authorize Android route-delta live capture. The live route-delta still requires a fresh exact operator gate and must use the checked Android flash/rollback path from V2364/V2365.

## Safety outcome

- No boot image was built or flashed.
- No device command was run.
- No Android boot or ADB session was attempted.
- No `tinymix set`, `tinyplay`, PCM playback/write, audio HAL live path, or `adsprpc` path was executed.
- Private JDK/SDK/DEX artifacts remain under `workspace/private/` only.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/bootstrap_android_audio_stimulus_toolchain_v2368.py tests/test_bootstrap_android_audio_stimulus_toolchain_v2368.py`
- `python3 -m unittest tests.test_bootstrap_android_audio_stimulus_toolchain_v2368 -v`
- `python3 workspace/public/src/scripts/revalidation/bootstrap_android_audio_stimulus_toolchain_v2368.py --dry-run`
- `python3 workspace/public/src/scripts/revalidation/bootstrap_android_audio_stimulus_toolchain_v2368.py --force-sdk-install`
- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_audio_route_stimulus_v2366.py tests/test_build_android_audio_route_stimulus_v2366.py`
- `PYTHONPATH=tests python3 -m unittest tests.test_build_android_audio_route_stimulus_v2366 -v`
- DEX build command above
- `file workspace/private/builds/audio/v2366-android-route-stimulus/A90AudioRouteStimulus.dex`
- `sha256sum workspace/private/builds/audio/v2366-android-route-stimulus/A90AudioRouteStimulus.dex`
- `native_audio_android_route_delta_handoff_v2365.py --dry-run --stimulus-dex workspace/private/builds/audio/v2366-android-route-stimulus/A90AudioRouteStimulus.dex`
