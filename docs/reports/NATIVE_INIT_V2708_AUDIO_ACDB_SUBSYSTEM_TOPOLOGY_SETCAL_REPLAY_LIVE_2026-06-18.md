# NATIVE_INIT V2708 — subsystem topology entry-cap ACDB SET replay live attempt

Date: 2026-06-18

## Scope

Rerun the checked V2639 native ACDB SET replay live handoff with the V2707
entry-cap deploy manifest. This is the follow-up to V2706, which failed before
ACDB ioctl replay because the staged helper artifact could not accept the 12-entry
sequence.

The V2708 live unit kept the established safety envelope:

- flash only the V2334 audio candidate through the checked helper;
- verify candidate health before audio work;
- boot ADSP and materialize `/dev/snd` nodes;
- stage the V2707 ACDB replay manifest and low-amplitude PCM probe artifacts;
- apply the bounded speaker route;
- run one ACDB SET replay helper and wait for final SET index 11;
- run one bounded low-amplitude PCM probe;
- wait for reverse deallocate cleanup, reset route controls, clean runtime state;
- rollback to V2321 and verify `selftest fail=0`.

## Result

- decision: `v2639-acdb-setcal-replay-live-blocked`
- interpreted V2708 decision: `v2708-acdb-setcal-replay-ok-pcm-open-blocked-asm-custom-topology-ebadparam`
- private manifest: `workspace/private/builds/audio/v2707-audio-acdb-subsystem-topology-entrycap-deploy-plan/deploy-plan.json`
- private run directory: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-193253`
- device action: live flash to V2334 candidate, ADSP boot/materialize, artifact stage, route apply, replay helper launch, PCM probe, route reset, runtime cleanup, rollback to V2321
- ACDB SET ioctl replay reached: `yes`
- final SET marker reached: `yes`, `A90_SETCAL_REPLAY_ALL_SET_OK pid=856 final_index=11`
- all replay SET ioctls returned OK: `yes`
- reverse deallocate cleanup returned OK: `yes`
- PCM probe attempted: `yes`
- PCM probe result: `blocked at pcm_open`
- rollback: `ok`
- rollback version: `v2321-usb-clean-identity-rodata`
- rollback selftest: `fail=0`

## Replay Evidence

V2708 fixed the V2706 helper artifact mismatch. All staged files passed SHA-256
verification on the device, and the helper reached the final SET index before the
PCM probe.

Replay stderr recorded these public-safe ACDB SET events:

| index | cal_type | size | result |
| --- | ---: | ---: | --- |
| 0 | 39 | 4916 | `AUDIO_SET_CALIBRATION ok` |
| 1 | 24 | 1180 | `AUDIO_SET_CALIBRATION ok` |
| 2 | 10 | 16076 | `AUDIO_SET_CALIBRATION ok` |
| 3 | 14 | 2356 | `AUDIO_SET_CALIBRATION ok` |
| 4 | 13 | 0 | `AUDIO_SET_CALIBRATION ok` |
| 5 | 9 | 0 | `AUDIO_SET_CALIBRATION ok` |
| 6 | 11 | 18084 | `AUDIO_SET_CALIBRATION ok` |
| 7 | 12 | 0 | `AUDIO_SET_CALIBRATION ok` |
| 8 | 15 | 28 | `AUDIO_SET_CALIBRATION ok` |
| 9 | 23 | 0 | `AUDIO_SET_CALIBRATION ok` |
| 10 | 16 | 1560 | `AUDIO_SET_CALIBRATION ok` |
| 11 | 21 | 28 | `AUDIO_SET_CALIBRATION ok` |

Cleanup markers confirmed reverse deallocation for allocated entries:

- `A90_ACDB_SETCAL_DEALLOCATE_OK index=10 cal_type=16`
- `A90_ACDB_SETCAL_DEALLOCATE_OK index=8 cal_type=15`
- `A90_ACDB_SETCAL_DEALLOCATE_OK index=6 cal_type=11`
- `A90_ACDB_SETCAL_DEALLOCATE_OK index=3 cal_type=14`
- `A90_ACDB_SETCAL_DEALLOCATE_OK index=2 cal_type=10`
- `A90_ACDB_SETCAL_DEALLOCATE_OK index=1 cal_type=24`
- `A90_ACDB_SETCAL_DEALLOCATE_OK index=0 cal_type=39`
- `A90_ACDB_SETCAL_REPLAY_DONE rc=0`

## PCM Failure Evidence

The bounded PCM probe failed at open time:

```text
A90_PCM_PROBE_START version=V2386 card=0 device=0 channels=2 rate=48000 bits=16 data_bytes=192000 period_size=1024 period_count=4
A90_PCM_PROBE_PCM_OPEN_ERROR card=0 device=0 pcm_error="cannot open device 0 for card 0: Cannot allocate memory"
pcm_hw_open: cannot open device '/dev/snd/pcmC0D0p'[exit 20]
ERR exit=20
```

The failure dmesg points at DSP rejection of the ASM custom topology:

```text
q6asm_callback: cmd = 0x10dbe returned error = 0x2
send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]
msm_pcm_open: Could not allocate memory
msm-pcm-dsp soc:qcom,msm-pcm: ASoC: can't open platform soc:qcom,msm-pcm: -12
SM8150 Media1: ASoC: failed to start FE -12
```

## Interpretation

This is a real ACDB replay result, not another pre-ACDB runner failure. The V2707
entry-cap helper artifact was staged, the expanded 12-entry replay sequence ran,
and all ACDB SET ioctls returned OK before the PCM probe.

The remaining block is now downstream at DSP validation of the ASM custom topology
sent during `pcm_open`. The kernel found enough calibration state to attempt the
ASM custom topology send, but the DSP rejected it with `ADSP_EBADPARAM`.

This strongly argues that the current synthetic/basic SET geometry for the custom
topology records is not byte-exact enough for the DSP, especially for the cal_type
14 ASM custom topology path. The captured GET payload bytes alone plus generic
basic SET headers are not sufficient to satisfy the DSP-side custom-topology
contract.

## Next Unit

Do not rerun V2639 with the same V2707 manifest unchanged. The next useful unit is
host-only design/analysis for byte-exact SET geometry capture or reconstruction for
the custom topology records, especially:

1. cal_type 14 ASM custom topology, because `send_asm_custom_topology` failed with
   `ADSP_EBADPARAM`;
2. cal_type 10 ADM custom topology;
3. cal_type 24 AFE custom topology.

The preferred direction is to capture or reconstruct the exact SET arg and payload
shape emitted by the Android ACDB loader around `acdb_loader_send_common_custom_topology`
and related subsystem-topology paths, then produce a new manifest only after the
SET geometry is pinned. Another replay of the GET blobs with the same generic SET
headers is not expected to add information.

## Validation

- rollback image SHA checks passed before live execution.
- preflight V2321 `selftest verbose`: `fail=0`.
- V2639 dry-run with the V2707 manifest: `execution_contract_ok=True`, `safe_to_run_native_replay=True`, `replay_gate_blockers=[]`.
- live candidate flash and health check passed.
- final SET marker reached before PCM probe.
- replay helper cleanup and reverse deallocation markers passed.
- route controls were reset and verified with no mismatches.
- runtime directory cleanup ran.
- rollback to V2321 completed.
- final V2321 selftest: `fail=0`.
