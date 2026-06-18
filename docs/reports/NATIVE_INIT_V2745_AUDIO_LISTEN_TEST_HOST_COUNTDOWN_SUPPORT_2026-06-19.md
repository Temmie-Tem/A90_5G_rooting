# NATIVE_INIT V2745 Audio Listen Test Host Countdown Support

## Purpose

Make the human-audible listen test operationally usable. V2743 added device-side listen-window markers, but the runner records remote stdout into step artifacts rather than streaming those markers to the operator before playback. That makes the actual listening window hard to catch.

## Change

- Added a host-side listen countdown before invoking the remote PCM playback wrapper.
- Default countdown: `5 s`.
- Hard cap: `10 s`.
- Host stdout emits JSON markers:
  - `A90_HOST_LISTEN_WINDOW_COUNTDOWN`
  - `A90_HOST_LISTEN_WINDOW_STARTING_NOW`
- The remote wrapper still emits `A90_LISTEN_WINDOW_READY`, `A90_LISTEN_WINDOW_BEGIN`, and `A90_LISTEN_WINDOW_END` into the run artifact.

## Safety

- No change to playback amplitude or route controls.
- Listen mode remains capped at amplitude `0.15` by default and `0.20` maximum.
- No WSA gain/boost writes are added.
- Non-listen/default playback remains unchanged.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py tests/test_native_audio_acdb_setcal_replay_live_handoff_v2639.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_setcal_replay_live_handoff_v2639 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --dry-run --listen-test --listen-countdown-sec 5 --v2636-manifest workspace/private/builds/audio/v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan/deploy-plan.json --manifest-path workspace/private/builds/audio/v2745-listen-countdown-support/dry-run-manifest.json`
- `git diff --check`

## Next

Run the bounded live listening test again. The operator should start listening when `A90_HOST_LISTEN_WINDOW_COUNTDOWN` appears and especially at `A90_HOST_LISTEN_WINDOW_STARTING_NOW`.
