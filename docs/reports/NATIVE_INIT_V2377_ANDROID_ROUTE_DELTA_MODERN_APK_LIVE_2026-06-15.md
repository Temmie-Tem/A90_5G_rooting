# NATIVE_INIT V2377 — Android Route-Delta Modern APK Live Capture

Date: 2026-06-15

## Purpose

Rerun the Android speaker route-delta handoff with the V2376 rebuilt modern-target APK. This tests whether the V2375 PermissionController blocker is gone and whether Android framework `AudioTrack` playback produces a usable `tinymix --all-values` route delta.

Magisk-module delivery was kept as a fallback only. This unit intentionally used the normal APK path first.

## Safety Envelope

- Device action: rollbackable Android boot handoff through `native_init_flash.py`, then rollback to V2321.
- Playback path: Android framework `AudioTrack` only.
- Explicitly not run: native `tinymix set`, native `/dev/snd` open/write, `tinyplay`, Wi-Fi/network actions, direct partition writes.
- Rollback target: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Final rollback health: V2321 `0.9.285`, `selftest fail=0`.

## Preconditions

Rollback and fallback images were present with expected SHA256:

| Image | SHA256 |
| --- | --- |
| V2321 rollback | `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb` |
| V2237 fallback | `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f` |
| V48 fallback | `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042` |

Resident preflight:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: pass=11 warn=1 fail=0
```

Dry-run gate:

```text
ok=True
live_ready=True
command_safety_ok=True
stimulus_mode=apk
apk_sha=fef87886bd1fb5f3dd07b857bbe3c4c00f9046f797ba9c84d48b89dc1d2d13f3
```

## Live Run

Private evidence directory:

```text
workspace/private/runs/audio/v2377-android-route-delta-modern-apk-20260615-042113/
```

Runner decision:

```text
decision=v2369-android-route-delta-live-captured-before-rollback
ok=True
rolled_back=True
```

Android boot, staging, APK install, baseline/active/post captures, APK uninstall, recovery reboot, and V2321 rollback all returned success.

## APK Stimulus Result

The V2376 target-SDK fix worked. The launch stayed on our Activity, not PermissionController:

```text
Activity: com.a90.nativeinit.audio/.A90AudioRouteStimulusActivity
Status: ok
WaitTime: 2562
```

Logcat markers:

```text
A90_AUDIO_STIMULUS_BEGIN=1
A90_AUDIO_STIMULUS_END=1
A90_AUDIO_STIMULUS_ERROR=0
A90_AUDIO_STIMULUS_FINISH=1
REVIEW_PERMISSIONS=0
```

Audio framework evidence:

```text
A90_AUDIO_STIMULUS_BEGIN duration_ms=2000 sample_rate=48000 amplitude=0.05 speaker_hint=true
AudioPlaybackConfiguration ... type:android.media.AudioTrack ... usage=USAGE_MEDIA content=CONTENT_TYPE_MUSIC ... state:started
player piid:103 state:device DeviceId:3 uid:10287
setCommunicationRouteForClient ... type:speaker ... Package Name:com.a90.nativeinit.audio
AudioTrack: stop(22): called with 96000 frames delivered
A90_AUDIO_STIMULUS_END frames=96000
A90_AUDIO_STIMULUS_FINISH rc=0
```

The unrelated `com.google.android.setupwizard` crash remains environmental noise from the stripped Android handoff and is not the stimulus process.

## Mixer Route Delta

`tinymix --all-values` changed during the active playback window:

| Phase | Lines | SHA256 |
| --- | ---: | --- |
| baseline | 3553 | `b60cf365b2b2fb948d1f91a9dfde5ae33fe81aa6719eba770bf1333cfe25509a` |
| active | 3554 | `dc75e58c2b4c31d583273341f7b5df135b6b596919ba8cb8b1db8eac344e7f11` |
| post | 3553 | `dd4ac12f4691f3267d2f1f22fb7b7e4d8eea9c979257c25e130024f4efc8edce` |

Stable route-relevant deltas:

| Control | Baseline | Active | Post |
| --- | --- | --- | --- |
| `COMP7 Switch` | `Off` | `On` | `Off` |
| `RX INT7_1 MIX1 INP0` | `>ZERO ... RX0 ...` | `ZERO ... >RX0 ...` | `>ZERO ... RX0 ...` |
| `AIF4_VI Mixer SPKR_VI_1` | `Off` | `On` | `Off` |
| `AIF4_VI Mixer SPKR_VI_2` | `Off` | `On` | `Off` |
| `SLIM RX0 MUX` | `>ZERO AIF1_PB ...` | `ZERO >AIF1_PB ...` | `>ZERO AIF1_PB ...` |
| `SLIMBUS_0_RX Audio Mixer MultiMedia1` | `Off Off` | `On Off` | `Off Off` |
| `SpkrLeft COMP Switch` | `Off` | `On` | `Off` |
| `SpkrLeft BOOST Switch` | `Off` | `On` | `Off` |
| `SpkrLeft VISENSE Switch` | `Off` | `On` | `Off` |
| `SLIM_4_TX Format` | `>UNPACKED PACKED_16B DSD_DOP` | `UNPACKED >PACKED_16B DSD_DOP` | `>UNPACKED PACKED_16B DSD_DOP` |
| `Playback Channel Map0` | all zero | `1 2 0 ...` | all zero |
| `Audio Stream 0 App Type Cfg` | all zero | `69941 15 48000 2 ...` | `69941 15 48000 2 ...` |
| `ADSP Path Latency 0` | `-1` | `58007` | `-1` |
| `SpkrLeft SWR DAC_Port Switch` | `Off` | `On` | `Off` |

Most route controls reverted after playback. `Audio Stream 0 App Type Cfg` persisted into post-capture, so treat it as stream calibration/config state rather than an active route switch.

## Interpretation

V2377 successfully identifies the Android speaker playback route for the tested framework `AudioTrack` path:

```text
MultiMedia1 -> SLIMBUS_0_RX -> SLIM RX0/AIF1_PB -> RX0 -> RX INT7 -> COMP7 -> SpkrLeft / SWR DAC path
```

This does not yet prove native-init playback, but it ends the Android stimulus-delivery blocker. Magisk-module stimulus delivery is no longer needed for this route-delta purpose; keep it only as a future fallback if a new Android handoff delivery wall appears.

## Validation

Commands run:

```text
python3 workspace/public/src/scripts/revalidation/a90_bridge.py status --json
python3 workspace/public/src/scripts/revalidation/a90ctl.py version
python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest verbose
python3 workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py --dry-run --stimulus-mode apk --stimulus-apk workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk
python3 workspace/public/src/scripts/revalidation/native_audio_android_route_delta_handoff_v2365.py --run-live --stimulus-mode apk --stimulus-apk workspace/private/builds/audio/v2373-android-route-stimulus-apk/A90AudioRouteStimulus.apk --approval 'AUD-3D2-android-route-delta go: rollbackable Android AudioTrack speaker route-delta capture, checked-helper boot handoff only, low-amplitude framework playback, no native speaker write, rollback to V2321'
python3 workspace/public/src/scripts/revalidation/a90ctl.py version
python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest verbose
```

Final health:

```text
version: 0.9.285 build=v2321-usb-clean-identity-rodata
selftest: pass=11 warn=1 fail=0
```

## Decision

`android-route-delta-modern-apk-pass-speaker-route-observed`

Next unit should be host-only: convert the observed Android mixer deltas into a guarded native-init route recipe and first-playback safety plan. Do not jump directly to native `tinymix set`/`tinyplay`; first define exact controls, order, reset sequence, amplitude bound, and abort conditions.
