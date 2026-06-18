# Native Init V2752 Audio App-Type Command

## Summary

- Cycle: `V2752`
- Track: audio productization Tier B command-surface migration, host-only.
- Decision: `v2752-audio-app-type-command-host-only-pass`
- Result: PASS
- Device flash: `no`.
- Device action: `none`.
- Private build check: `workspace/private/builds/native-init/v2752-audio-app-type-command/a90_audio.o`
- Private object SHA256: `ef00247c5ca56a3149e8115afd39ea02247593ba1194541aebeb2a4f8788092d`

## Change

- Adds `audio app-type [profile] [--dry-run|--write]` to native-init.
- Moves the decisive V2748 global `App Type Config` operation from host-pushed helper logic toward native-init command surface.
- Reuses the V2751 `internal-speaker-safe` profile values instead of re-encoding a separate constant set:
  - profile: `internal-speaker-safe`
  - card: `0`
  - control: `App Type Config`
  - payload: `1 69941 48000 16`
- Uses one atomic `SNDRV_CTL_IOCTL_ELEM_WRITE` over `/dev/snd/controlC0`, matching the V2733 writer rationale and avoiding per-index `tinymix` writes on the write-only multi-value control.
- Default mode is `--dry-run`; the command performs no ALSA write unless `--write` is explicit.

## Safety Boundary

- Host-only source/API unit.
- No boot image was flashed.
- No ADSP activation, `/dev/snd` materialization, mixer write, ACDB SET, PCM playback, tinyalsa, HAL, Wi-Fi, network, or partition write occurred.
- Runtime write mode is explicit (`--write`) and uses only the known-good global App-Type-Config tuple; it does not change WSA gain/boost/protection controls.
- This is not yet `audio route` or `audio play`; it is the reusable native primitive that those commands should call next.

## Validation

- `aarch64-linux-gnu-gcc -std=gnu99 -Wall -Wextra -Werror -fsyntax-only -I workspace/public/src/native-init workspace/public/src/native-init/a90_audio.c`: PASS
- `aarch64-linux-gnu-gcc -std=gnu99 -Wall -Wextra -Werror -I workspace/public/src/native-init -c workspace/public/src/native-init/a90_audio.c -o workspace/private/builds/native-init/v2752-audio-app-type-command/a90_audio.o`: PASS
- `file workspace/private/builds/native-init/v2752-audio-app-type-command/a90_audio.o`: `ELF 64-bit LSB relocatable, ARM aarch64`
- `python3 -m py_compile tests/test_native_audio_app_type_command_v2752.py tests/test_native_audio_command_profile_contract_v2751.py workspace/public/src/scripts/revalidation/native_audio_speaker_profiles_v2749.py workspace/public/src/scripts/revalidation/native_audio_speaker_feature_entrypoint_v2750.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_app_type_command_v2752 tests.test_native_audio_command_profile_contract_v2751 tests.test_native_audio_speaker_profiles_v2749 tests.test_native_audio_speaker_feature_entrypoint_v2750 -v`: PASS, 18 tests.
- `git diff --check`: PASS.

## Next Step

- Implement `audio route <profile>` so it calls the native `audio app-type ... --write` primitive internally and then applies the known V2378/V2639 route control sequence with bounded reset/cleanup semantics.
