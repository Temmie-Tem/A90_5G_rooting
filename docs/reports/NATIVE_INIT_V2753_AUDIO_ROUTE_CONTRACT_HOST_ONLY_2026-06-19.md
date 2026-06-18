# NATIVE_INIT V2753 — Audio Route Contract Host-Only

Date: 2026-06-19
Scope: host-only native-init audio command surface
Baseline context: V2748 proved audible internal-speaker playback; V2749–V2752 began productizing the path into profile and app-type APIs.

## Decision

Add a first-class `audio route [profile] [--dry-run|--apply|--reset]` command contract, but intentionally block all route write modes for this unit.

Reason: the proven V2378/V2748 internal-speaker route includes `SpkrLeft BOOST Switch`. The active `GOAL.md` safety boundary explicitly forbids WSA smart-amp gain/boost writes until speaker protection is fully characterized. Therefore V2753 exposes the route plan as an API-like surface while refusing `--apply` and `--reset` with:

```text
audio.route.refused=write-mode-blocked-smart-amp-boost-review
```

No device action, no ALSA route write, no boot image build, and no flash were performed.

## Implemented Contract

Touched public source:

- `workspace/public/src/native-init/a90_audio.c`
- `tests/test_native_audio_command_profile_contract_v2751.py`
- `tests/test_native_audio_route_contract_v2753.py`

Command exposed:

```text
audio route [profile] [--dry-run|--apply|--reset]
```

Default mode: `--dry-run`.

Route profile: `internal-speaker-safe`.

Pinned route metadata:

- apply count: `13`
- reset count: `12`
- requires global app-type primitive: `audio app-type internal-speaker-safe --write`
- write attempted before refusal: `0`
- smart-amp boost blocker: `SpkrLeft BOOST Switch`

## Pinned Apply Route

Source: V2378 route recipe used by the audible V2748 path.

1. `Audio Stream 0 App Type Cfg` → `69941 15 48000 2`, zero-fill to 128
2. `Playback Channel Map0` → `1 2`, zero-fill to 32
3. `SLIMBUS_0_RX Audio Mixer MultiMedia1` → `1 0`
4. `SLIM RX0 MUX` → `AIF1_PB`
5. `RX INT7_1 MIX1 INP0` → `RX0`
6. `COMP7 Switch` → `1`
7. `AIF4_VI Mixer SPKR_VI_1` → `1`
8. `AIF4_VI Mixer SPKR_VI_2` → `1`
9. `SLIM_4_TX Format` → `PACKED_16B`
10. `SpkrLeft VISENSE Switch` → `1`
11. `SpkrLeft COMP Switch` → `1`
12. `SpkrLeft BOOST Switch` → `1` (**blocked for write review**)
13. `SpkrLeft SWR DAC_Port Switch` → `1`

Reset order is emitted in reverse and skips non-resettable `Audio Stream 0 App Type Cfg`, matching the V2378 reset contract.

## Validation

Commands:

```bash
mkdir -p workspace/private/builds/native-init/v2753-audio-route-contract
aarch64-linux-gnu-gcc -std=gnu99 -Wall -Wextra -Werror -fsyntax-only \
  -I workspace/public/src/native-init workspace/public/src/native-init/a90_audio.c
aarch64-linux-gnu-gcc -std=gnu99 -Wall -Wextra -Werror \
  -I workspace/public/src/native-init -c workspace/public/src/native-init/a90_audio.c \
  -o workspace/private/builds/native-init/v2753-audio-route-contract/a90_audio.o
file workspace/private/builds/native-init/v2753-audio-route-contract/a90_audio.o
sha256sum workspace/private/builds/native-init/v2753-audio-route-contract/a90_audio.o
python3 -m py_compile \
  tests/test_native_audio_route_contract_v2753.py \
  tests/test_native_audio_app_type_command_v2752.py \
  tests/test_native_audio_command_profile_contract_v2751.py \
  workspace/public/src/scripts/revalidation/native_audio_speaker_profiles_v2749.py \
  workspace/public/src/scripts/revalidation/native_audio_speaker_feature_entrypoint_v2750.py
PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest \
  tests.test_native_audio_route_contract_v2753 \
  tests.test_native_audio_app_type_command_v2752 \
  tests.test_native_audio_command_profile_contract_v2751 \
  tests.test_native_audio_speaker_profiles_v2749 \
  tests.test_native_audio_speaker_feature_entrypoint_v2750 -v
```

Result:

- `a90_audio.c` syntax-only compile: pass
- AArch64 object build: pass
- object type: `ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped`
- object SHA256: `21c6ffb61404e7e6cfd00d588b9532130a4a4454afa8a880861ed8a3ec987105`
- Python py_compile: pass
- unittest: `Ran 24 tests ... OK`

## Next Step

Split route productization into two explicit layers:

1. **Safe base route primitive:** controls that do not hit WSA smart-amp boost/gain policy.
2. **Speaker endpoint policy:** `VISENSE`/`COMP`/`BOOST`/SWR endpoint controls, with a clear operator-reviewed rule before any `BOOST` write is shipped.

Only after that split should `audio route --apply` move from refused contract to live write path.
