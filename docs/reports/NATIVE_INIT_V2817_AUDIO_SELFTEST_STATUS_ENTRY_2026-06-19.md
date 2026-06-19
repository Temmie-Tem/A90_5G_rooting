# Native Init V2817 Audio Selftest Status Entry

## Summary

- Run ID: `V2817`
- Track: post-promotion audio Tier C observability.
- Device flash: no.
- Scope: add a read-only `audio` selftest entry that summarizes the promoted audio-core profile and safety contract without touching ADSP, ALSA, route controls, ACDB, or PCM.

## Change

- Promoted audio-core metadata is centralized in `a90_audio_profile.h`:
  - `AUDIO_CORE_PROMOTION_RUN=V2815`
  - `AUDIO_CORE_PROMOTION_VERSION=0.10.0`
  - `AUDIO_CORE_PROMOTION_TAG=v2812-audio-core-promotion-candidate`
  - `AUDIO_CORE_VALIDATION_RUN=V2814`
- `selftest verbose` gains an `audio` row that checks the compiled default profile, route count, speaker map count, amplitude cap, duration cap, and smart-amp boost block policy.
- The new selftest entry is read-only and static-contract-only. It does not open audio device nodes, issue ioctls, apply routes, replay ACDB SETs, or start playback.

## Validation

- `python3 -m py_compile tests/test_native_audio_selftest_status_v2817.py`
- Focused unittest: `tests.test_native_audio_selftest_status_v2817`
- Existing focused unittest: `tests.test_native_audio_command_profile_contract_v2751`
- AArch64 object compile for `a90_audio.c` and `a90_selftest.c`
- `git diff --check`

## Next

- A future flashed artifact can expose this selftest row on-device. Because this source change would alter the boot artifact when built, assign a new run/build identity before any flash.
