# NATIVE_INIT_V2451_AUDIO_ACDB_M1_HYBRID_LATE_OBSERVER_DESIGN_2026-06-15

## Summary

V2451 implements the host-only hybrid M1 late-observer handoff for the Android-good
`/dev/msm_audio_cal` payload capture frontier.

V2450 proved the diagnostic helper can trace Android audio processes, but the temporary
Magisk boot service starts at Android boot and can age out before host-triggered
AudioTrack playback after the long post-module ADB/root settle. V2451 keeps that boot
service as an optional early observer and adds a host-coordinated late observer from the
already staged module helper.

## Direction

Magisk remains a Wi-Fi-style Android-good measurement capsule only:

- It is used to stage and run Android-side measurement helpers under stock Android.
- It is not a native-init runtime dependency.
- It does not issue native calibration ioctls.
- It does not write native mixer or PCM state.
- It does not call `magisk --install-module`.

Native ACDB replay remains blocked until payload order, decoded headers, payload hashes,
mem-handle policy, and cleanup policy are pinned from Android-good evidence.

## Implementation

Added:

- `workspace/public/src/scripts/revalidation/native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py`
- `tests/test_native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py`

The V2451 runner reuses the V2450 checked Android handoff, staging, cleanup, and V2321
rollback path. It adds two commands:

- `start_late_diag_observer_after_post_module_settle`
- `wait_for_late_diag_helper_completion`

The late observer:

- runs after post-module ADB/root settle;
- starts before AudioTrack playback;
- launches a background supervisor under `su -c`;
- targets `android.hardware.audio.service` and `audioserver`;
- runs the staged `a90_acdb_ioctl_capture_diag_v2449` helper with `--fd-pid` and
  `/dev/msm_audio_cal` filtering;
- writes late JSONL files named `msm-audio-cal-diag-threadset-p${pid}-late.jsonl`;
- waits for helper terminal `stop` records before artifact collection.

## Classification

V2451 keeps the V2450 boot-service artifact parser, but adds a late-observer subset
classifier. Late payload capture overrides an early boot-service partial classification so
old `partial-helper-still-running` artifacts do not hide the late result.

No raw payload bytes are included in public summaries; only hashes and metadata are kept.

## Live Gate

Future live execution requires this exact phrase:

`AUD-5L-acdb-m1-hybrid-late-observer go: rollbackable Android AudioTrack speaker msm_audio_cal diagnostic ioctl capture with temporary Magisk service module plus host-coordinated late observer, helper-completion wait, no native calibration ioctl, no native speaker write, rollback to V2321`

## Validation

Host-only validation performed:

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py tests/test_native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py`
- `PYTHONPATH=tests python3 -m unittest tests/test_native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py`
- `PYTHONPATH=tests python3 -m unittest tests/test_native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py tests/test_native_audio_acdb_m1_diag_observer_live_handoff_v2450.py`
- `PYTHONPATH=tests python3 -m unittest discover -s tests` (`1240` tests)
- `python3 workspace/public/src/scripts/revalidation/native_audio_acdb_m1_hybrid_late_observer_live_handoff_v2451.py --dry-run --materialize-module-template`

Materialized dry-run result:

- `run_id=V2451`
- `future_live_ready=true`
- `command_safety_ok=true`
- `module_id=a90_audio_acdb_m1_diag_v2449`
- `late_observer=true`

No device action was run in this unit.
