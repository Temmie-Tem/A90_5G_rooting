# NATIVE_INIT_V2762_AUDIO_STOP_PLAN_API_HOST_ONLY_2026-06-19

## Decision

`audio stop` now exists as a first-class native-init command surface for speaker cleanup planning. It is dry-run only; actual PCM stop, reverse ACDB deallocation, and route reset orchestration remain blocked until the native SET executor and playback executor are implemented.

## What changed

- Added `audio stop [profile] [--dry-run|--execute]`.
- Added native stage `plan-audio-stop-cleanup` between blocked playback and core route reset.
- The dry-run command reports the required cleanup sequence: PCM stop, reverse ACDB deallocation order, and core route reset command.
- `--execute` remains refused with `execute-not-implemented-native-cleanup`.

## Safety boundary

This is host-only/static behavior. The stop command does not open ALSA, does not issue ALSA ioctls, does not issue calibration ioctls, does not write mixer controls, and does not flash or run on-device.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_speaker_profiles_v2749.py tests/test_native_audio_stop_plan_api_v2762.py tests/test_native_audio_stage_api_contract_v2756.py tests/test_native_audio_command_profile_contract_v2751.py` passed.
- `PYTHONPATH=tests python3 -m unittest tests.test_native_audio_stop_plan_api_v2762 tests.test_native_audio_stage_api_contract_v2756 tests.test_native_audio_command_profile_contract_v2751` passed: 15 tests.
- `PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_native_audio_*v27*.py'` passed: 124 tests.
- `aarch64-linux-gnu-gcc -std=gnu11 -Wall -Wextra -Werror -Iworkspace/public/src/native-init -c workspace/public/src/native-init/a90_audio.c -o /tmp/a90_audio_v2762.o` passed.
- `/tmp/a90_audio_v2762.o` SHA-256: `538aeb1818dba7a3615c851b5504913303ea84b6001647064a72117aaf2dcac9`.
- `git diff --check` passed.
