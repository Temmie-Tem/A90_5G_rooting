# NATIVE_INIT_V2764_AUDIO_SPEAKER_MAP_API_HOST_ONLY_2026-06-19

## Scope

Host-only Audio Tier-C readability/API unit. This adds a first-class read-only
`audio speaker-map [profile]` command so the proven internal-speaker path can be
inspected by speaker/route grouping instead of archaeology through the route
array.

No device action, flash, playback, mixer write, route write, `/dev/ion` open,
`/dev/msm_audio_cal` open, or calibration ioctl occurred.

## Changes

- Added `audio speaker-map [profile]` dispatch and usage surface.
- Added a read-only speaker map table for:
  - `shared`
  - `SPKR_VI_1`
  - `SPKR_VI_2`
  - `SPKR_VI`
  - `SpkrLeft`
  - `SpkrRight`
- The command reports, per speaker id:
  - total route controls;
  - core/feedback/endpoint route controls;
  - blocked smart-amp boost controls;
  - matching observer controls.
- The command also reports hardware/path metadata and safety fields:
  - `SpkrLeft/SpkrRight WSA881x via WSA_CDC_DMA_RX`;
  - `SLIMBUS_0_RX_to_WSA_CDC_DMA_RX`;
  - amplitude cap;
  - `smart_amp_boost_write_allowed=0`.

## Safety Boundary

`audio speaker-map` is read-only. It does not call `open()`, does not call
`ioctl()`, and explicitly prints `route_write_attempted=0` and
`playback_attempted=0`. It exposes the current route/observer policy, including
that smart-amp boost remains blocked.

## Validation

```bash
python3 -m py_compile \
  tests/test_native_audio_speaker_map_api_v2764.py \
  tests/test_native_audio_command_profile_contract_v2751.py

PYTHONPATH=tests python3 -m unittest \
  tests.test_native_audio_speaker_map_api_v2764 \
  tests.test_native_audio_command_profile_contract_v2751 \
  tests.test_native_audio_route_layer_policy_v2754
# Ran 13 tests: OK

PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_native_audio_*v27*.py'
# Ran 131 tests: OK

aarch64-linux-gnu-gcc -std=gnu11 -Wall -Wextra -Werror \
  -Iworkspace/public/src/native-init \
  -c workspace/public/src/native-init/a90_audio.c \
  -o /tmp/a90_audio_v2764.o
file /tmp/a90_audio_v2764.o
# ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
sha256sum /tmp/a90_audio_v2764.o
# ad19b29747a548bfcb7bad1a3dd53ee9e87936e6829d8b4c4429aaf1924e18ca
```

## Result

The audio command surface now has a speaker/route map API suitable for readable
operation and later UI/status integration. It makes the current left/right,
feedback, endpoint, and blocked-boost split explicit without touching runtime
audio state.
