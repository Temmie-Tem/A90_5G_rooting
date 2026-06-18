# Native Init V2751 Audio Native Profile Contract

## Summary

- Cycle: `V2751`
- Track: audio productization Tier A/B bridge, host-only.
- Decision: `v2751-audio-native-profile-contract-host-only-pass`
- Result: PASS
- Device flash: `no`.
- Device action: `none`.
- Private build check: `workspace/private/builds/native-init/v2751-audio-profile-contract/a90_audio.o`
- Private object SHA256: `11a5ba992af92127e79efbf2ae99beae8a52b702d60e038af36f262da40ed077`

## Change

- Adds a native-init audio speaker profile table to `a90_audio.c`.
- Adds read-only command surface:
  - `audio profiles`
  - `audio profile [internal-speaker-safe]`
- Pins the proven internal speaker contract in native code:
  - endpoint: `internal-speaker`
  - speaker map: `SpkrLeft/SpkrRight WSA881x via WSA_CDC_DMA_RX`
  - PCM: `card=0`, `device=0`, `channels=2`, `sample_rate=48000`, `bit_width=16`
  - global App-Type-Config: `1 69941 48000 16`
  - stream App-Type-Config: `69941 15 48000 2`
  - ACDB SET order: `39,20,20,13,9,11,12,15,23,16,21`
  - stale/forbidden cal types: `10,14,24`
- `audio status` now reports `audio.status.default_profile=internal-speaker-safe`.

## Safety Boundary

- Host-only source/API unit.
- No boot image was flashed.
- No ADSP activation, `/dev/snd` materialization, mixer write, ACDB SET, PCM playback, tinyalsa, HAL, Wi-Fi, network, or partition write occurred.
- Profile is read-only metadata. It does not route, play, or stop audio yet.
- Speaker safety remains capped at `amplitude_milli<=200` and `duration_ms<=10000`; no smart-amp gain/boost changes are introduced.

## Validation

- `aarch64-linux-gnu-gcc -std=gnu99 -Wall -Wextra -Werror -fsyntax-only -I workspace/public/src/native-init workspace/public/src/native-init/a90_audio.c`: PASS
- `aarch64-linux-gnu-gcc -std=gnu99 -Wall -Wextra -Werror -I workspace/public/src/native-init -c workspace/public/src/native-init/a90_audio.c -o workspace/private/builds/native-init/v2751-audio-profile-contract/a90_audio.o`: PASS
- `file workspace/private/builds/native-init/v2751-audio-profile-contract/a90_audio.o`: `ELF 64-bit LSB relocatable, ARM aarch64`
- `python3 -m py_compile tests/test_native_audio_command_profile_contract_v2751.py workspace/public/src/scripts/revalidation/native_audio_speaker_profiles_v2749.py workspace/public/src/scripts/revalidation/native_audio_speaker_feature_entrypoint_v2750.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_command_profile_contract_v2751 tests.test_native_audio_speaker_profiles_v2749 tests.test_native_audio_speaker_feature_entrypoint_v2750 -v`: PASS, 14 tests.
- `git diff --check`: PASS.

## Next Step

- Use this profile contract as the native source of truth for the next Tier-B unit: a bounded `audio route <profile>` or `audio play <tone|builtin>` implementation that consumes the profile instead of re-encoding constants in host scripts.
