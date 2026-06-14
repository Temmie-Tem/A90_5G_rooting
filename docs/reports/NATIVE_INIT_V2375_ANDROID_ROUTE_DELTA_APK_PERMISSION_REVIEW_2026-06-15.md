# NATIVE_INIT V2375 — Android route-delta APK-mode live capture hit permission review

## Scope

V2375 used the overnight pre-authorized Android route-delta path with the V2374 APK-mode runner. The run stayed inside the recoverable envelope:

- checked-helper Android boot handoff only,
- boot partition only,
- low-amplitude Android framework `AudioTrack` stimulus path only,
- no native speaker write,
- no native `tinymix set`, PCM open/write, `/dev/snd` write, `tinyplay`, Wi-Fi, credentials, DHCP, routes, or ping,
- rollback to V2321 and final native selftest.

## Run Artifact

Private evidence directory:

```text
workspace/private/runs/audio/v2375-android-route-delta-apk-20260615-040901/
```

The runner still records its internal historical live tag as `V2369`; this report is the V2375 live execution record.

## Preflight

- Worktree was clean before live execution.
- Rollback images verified:
  - V2321 SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - V2237 SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - V48 SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- Resident V2321 health before the run: `selftest fail=0`, version `0.9.285`.
- `adb devices -l` was empty before Android boot, so no host-side wrong-device ambiguity was present.
- APK-mode dry-run reported:
  - `ok=True`
  - `live_ready=True`
  - `command_safety.ok=True`
  - `live_blockers=[]`
  - APK SHA256 `d5543153b497087c7145d25c81bd8c874e23e380a1e5af4358f8dda0257b08af`

## Execution Result

Runner result:

```text
decision=v2369-android-route-delta-live-captured-before-rollback
ok=True
rolled_back=True
steps=29
```

Major phases:

| Phase | Result |
| --- | --- |
| Flash Android boot | `rc=0`, Android root check passed |
| Stage `tinymix` | `rc=0` |
| Install APK | `rc=0`, `adb install -r` success |
| Baseline snapshots | `tinymix`, `dumpsys`, `/proc/asound` captured |
| APK Activity launch | `am start` returned `rc=0`, but launched PermissionController review |
| Active/post snapshots | captured |
| Cleanup | temp dir removed, APK uninstalled |
| Android reboot recovery | `rc=0` |
| V2321 rollback | `rc=0` |
| Final V2321 health | `selftest fail=0`, version `0.9.285` |

## Finding

The APK delivery path fixed the `app_process` rc `137` process-kill problem, but it did not yet execute the stimulus Activity. Android redirected the launch to permission review:

```text
Activity: com.google.android.permissioncontroller/com.android.permissioncontroller.permission.ui.ReviewPermissionsActivity
```

Logcat confirms the requested launch and the review detour:

```text
START u0 {act=com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS ... cmp=com.a90.nativeinit.audio/.A90AudioRouteStimulusActivity ...} from uid 0
wm_create_activity: ... com.google.android.permissioncontroller/com.android.permissioncontroller.permission.ui.ReviewPermissionsActivity,android.intent.action.REVIEW_PERMISSIONS,... startActivityAndWait:com.android.shell
```

No stimulus markers appeared:

```text
A90_AUDIO_STIMULUS_BEGIN=0
A90_AUDIO_STIMULUS_END=0
A90_AUDIO_STIMULUS_ERROR=0
A90_AUDIO_STIMULUS_FINISH=0
```

No active AudioFlinger/package evidence appeared:

```text
active-dumpsys-audio pkg_mentions=0
active-dumpsys-audioflinger pkg_mentions=0
active-dumpsys-audiopolicy pkg_mentions=0
```

## Root Cause

The APK manifest does not declare `uses-sdk`, so the built APK is treated as a very old target SDK. Host-side `aapt dump badging` shows Android adding implied dangerous permissions:

```text
uses-permission: name='android.permission.WRITE_EXTERNAL_STORAGE'
uses-implied-permission: name='android.permission.WRITE_EXTERNAL_STORAGE' reason='targetSdkVersion < 4'
uses-permission: name='android.permission.READ_PHONE_STATE'
uses-implied-permission: name='android.permission.READ_PHONE_STATE' reason='targetSdkVersion < 4'
uses-permission: name='android.permission.READ_EXTERNAL_STORAGE'
uses-implied-permission: name='android.permission.READ_EXTERNAL_STORAGE' reason='requested WRITE_EXTERNAL_STORAGE'
```

Those implied permissions are enough to trigger Android's permission review UI on first launch, preventing the test Activity from reaching `onCreate()`.

## Mixer Delta

No route delta was observed because the stimulus never ran. The three `tinymix -D 0 --all-values` outputs are byte-identical:

```text
baseline sha256=b60cf365b2b2fb948d1f91a9dfde5ae33fe81aa6719eba770bf1333cfe25509a
active   sha256=b60cf365b2b2fb948d1f91a9dfde5ae33fe81aa6719eba770bf1333cfe25509a
post     sha256=b60cf365b2b2fb948d1f91a9dfde5ae33fe81aa6719eba770bf1333cfe25509a
changed_lines=0
controls/header lines=3553
```

## Final Native Health

After rollback, direct serial bridge checks showed:

```text
version: A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)
selftest: fail=0
```

## Decision

```text
android-route-delta-apk-blocked-by-permission-review
```

Next unit should fix the APK manifest/build by declaring an explicit modern `uses-sdk` target, then rebuild the private APK and rerun the same preauthorized route-delta path. Magisk-module delivery remains a follow-on only if a normal modern-target APK still cannot launch the framework AudioTrack stimulus; it is not justified before this manifest fix.
