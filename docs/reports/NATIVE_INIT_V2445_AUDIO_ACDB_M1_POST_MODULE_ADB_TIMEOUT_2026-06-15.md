# NATIVE_INIT_V2445_AUDIO_ACDB_M1_POST_MODULE_ADB_TIMEOUT_2026-06-15

## Summary

V2445 ran the exact-gated M1 Android/Magisk ACDB payload-capture route using the V2444
runner. The V2444 service-duration clamp was present in the staged module, and module
staging/install passed with exact SHA validation. The run did not reach logcat capture,
AudioTrack playback, or artifact pull because ADB did not reappear within the runner's
`120s` post-module reboot `adb wait-for-device` budget.

This is a timing/settle-budget wall, not a staging, cleanup, or rollback failure. The
same ADB device reappeared during the cleanup `finally` path shortly after the timed-out
settle step, cleanup removed the temporary module and run directory, and the checked V2321
rollback succeeded. Independent native health after rollback returned V2321 with
`selftest fail=0`.

No native speaker/mixer/PCM write, no native `/dev/msm_audio_cal` ioctl, no native ACDB
replay, and no Wi-Fi action was performed.

## What Passed

Private run directory:

```text
workspace/private/runs/audio/v2445-acdb-m1-magisk-module-retry-20260615-145726
```

Preflight before live:

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` SHA matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` SHA matched
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` was present.
- Resident native state before handoff was V2321 with `selftest fail=0`.
- Materialized V2444 dry-run returned `future_live_ready=true` and command safety clean.

Live path passed through:

- Checked Android boot handoff.
- Android post-handoff settle and Magisk root check before staging.
- Module/APK staging.
- Exact incoming SHA validation for all four module files:
  - `module.prop` SHA `46fc54b76f605f7ee09692981ed86626b7a30af229797c82d10d42e55f26f6dd`
  - `service.sh` SHA `f94ed1949b7d738dc0f9a2ca12456bbec8913fef516899e102cbd97f45a409f7`
  - `README.md` SHA `aa9237b16cb21d52d81d16d6c7f7cf8ad1cdb96fdd7cae7dcdbd489a68f84607`
  - `a90_acdb_ioctl_capture_threadset_v2423` SHA
    `80206c64f7783384be06baa508c03f9492e8c420c6a867821fa8379d5b0f6d9a`
- Final module install marker:
  - `A90_M1_INSTALL_OK`
- Cleanup after the timeout:
  - `cleanup-finally-0` `adb wait-for-device`: passed after `86.292s`.
  - `cleanup-finally-2`: `A90_M1_CLEANUP_OK`.
  - `cleanup-finally-3`: module dir and run dir absent.
- Checked rollback:
  - `rollback-v2321`: `ok=true`, elapsed `67.520s`.
- Independent post-run health:
  - `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
  - `selftest: pass=11 warn=1 fail=0`

## Failure Point

The exact failure was before logcat/playback/artifact collection:

```text
decision: v2444-acdb-m1-magisk-module-retry-failed-before-rollback
error: android-post-module-reboot-settle-0-wait-for-device timed out after 120.0s
```

Timeline facts:

```text
android-reboot-for-magisk-service finished: 2026-06-15T14:58:43.609642+09:00
post-module wait-for-device timeout file: 2026-06-15T15:00:43.676...
cleanup-finally-0 started: 2026-06-15T15:00:43.677431+09:00
cleanup-finally-0 finished: 2026-06-15T15:02:09.969061+09:00
```

Therefore Android ADB returned approximately `206.359s` after the module-activation reboot
finished. The runner's post-module settle budget was `120s`, so it gave up about `86s` too
early. Because cleanup then immediately used the same ADB path successfully, the evidence
points to slow post-module Android/ADB enumeration rather than a persistent boot failure.

## Payload Capture Summary

No payload capture window ran:

- No logcat capture around the stimulus.
- No AudioTrack playback.
- No artifact pull.
- `payload_capture_summary` is absent from `result.json`.
- The V2444 duration clamp was staged but not functionally exercised because the
  `service.sh` activation window was not reached before the runner timed out.

## Next Unit

V2446 should be host-only runner hardening before any further live rerun:

- Extend the post-module `adb wait-for-device` budget above the observed `206s` return time
  or implement a bounded multi-attempt wait that records the late-return classification.
- Preserve V2444's duration clamp, V2442's correct post-module boundary, staging/install,
  cleanup, rollback, and native-audio safety boundaries unchanged.
- Add a focused test proving the post-module wait timeout is no longer the generic
  `adb_command_timeout=120` value.
- Re-run materialized dry-run and full tests before another exact-gated live attempt.

Do not proceed to native replay, native calibration ioctl, or native speaker writes. The
frontier remains Android-good measurement of the real `/dev/msm_audio_cal` payload sequence.
