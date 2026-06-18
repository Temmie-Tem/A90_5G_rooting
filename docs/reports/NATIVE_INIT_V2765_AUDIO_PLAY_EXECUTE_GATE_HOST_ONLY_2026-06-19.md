# NATIVE_INIT_V2765_AUDIO_PLAY_EXECUTE_GATE_HOST_ONLY_2026-06-19

## Scope

Host-only Audio Tier-B boundary unit. This turns `audio play --execute` from a
plain refusal into a PCM executor gate: after profile/mode validation and safety
cap checks, it emits the exact bounded PCM geometry and future execution sequence,
then refuses before opening ALSA or writing samples.

No device action, flash, playback, mixer write, ALSA open, PCM ioctl, PCM write,
`/dev/ion` open, `/dev/msm_audio_cal` open, or calibration ioctl occurred.

## Changes

- Added pinned PCM geometry constants:
  - `AUDIO_PCM_PERIOD_SIZE = 1024`
  - `AUDIO_PCM_PERIOD_COUNT = 4`
- Added internal helpers for frame and data byte calculation from the selected
  speaker profile and bounded duration.
- `audio play --execute` now prints `audio.play.execute.plan.*` fields:
  - PCM path `/dev/snd/pcmC%dD%dp`;
  - period size/count;
  - frame bytes, period bytes, total data bytes, and chunk count;
  - selected amplitude/duration;
  - bounded-tone waveform label;
  - future sequence `open_pcm,configure_hw_params,write_bounded_tone,drain,close_pcm`.
- The command still refuses with `execute-not-implemented-native-pcm` before
  runtime access.

## Safety Boundary

The execute gate is still non-mutating. The plan function does not call `open()`,
`ioctl()`, or `write()`, and it reports:

- `audio.play.execute.plan.alsa_open_attempted=0`
- `audio.play.execute.plan.ioctl_attempted=0`
- `audio.play.execute.plan.pcm_write_attempted=0`

Safety cap checks still run before the execute plan. Amplitude remains capped by
the profile at `<=0.2`.

## Validation

```bash
python3 -m py_compile \
  tests/test_native_audio_play_execute_gate_v2765.py \
  tests/test_native_audio_play_plan_api_v2761.py

PYTHONPATH=tests python3 -m unittest \
  tests.test_native_audio_play_execute_gate_v2765 \
  tests.test_native_audio_play_plan_api_v2761 \
  tests.test_native_audio_speaker_map_api_v2764
# Ran 13 tests: OK

PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_native_audio_*v27*.py'
# Ran 134 tests: OK

aarch64-linux-gnu-gcc -std=gnu11 -Wall -Wextra -Werror \
  -Iworkspace/public/src/native-init \
  -c workspace/public/src/native-init/a90_audio.c \
  -o /tmp/a90_audio_v2765.o
file /tmp/a90_audio_v2765.o
# ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
sha256sum /tmp/a90_audio_v2765.o
# decdd47aa791df1a018a589cdb9881742b9128240d98f378a49a34d2a9fa7b5f
```

## Result

`audio play --execute` now has a concrete native PCM executor boundary. The next
implementation unit can replace the final refusal with a bounded ALSA PCM writer
without changing the profile safety contract or PCM geometry contract.
