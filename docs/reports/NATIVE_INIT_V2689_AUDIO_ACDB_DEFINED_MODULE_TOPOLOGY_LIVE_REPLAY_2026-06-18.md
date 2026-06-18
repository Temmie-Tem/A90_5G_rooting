# NATIVE_INIT V2689 — ACDB defined-module topology live replay

Date: 2026-06-18

## Scope

Live native-init replay using the V2688 manifest. This run preserves the V2684/V2686 ACDB SET order but replaces only cal_type `10` and `14` topology payloads with the V2687 defined-modules-only candidates. It keeps the existing bounded route/PCM probe contract: one-shot SET replay, low-amplitude PCM probe, reverse deallocate cleanup, route reset, checked rollback to V2321.

## Result

- decision: `v2689-defined-module-topology-replay-still-adsp-ebadparam`
- ACDB SET replay: `completed`, final marker `A90_SETCAL_REPLAY_ALL_SET_OK pid=858 final_index=11`
- replaced payloads: cal_type `10` topology `0x10004000`, cal_type `14` topology `0x10005000`
- PCM probe: `failed`, `A90_PCM_PROBE_PCM_OPEN_ERROR`, exit codes `[20, 20]`
- kernel marker: `send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]`
- cleanup: reverse deallocate succeeded for payload indices `[0, 1, 2, 3, 6, 8, 10]`
- rollback: checked V2321 flash/readback/boot succeeded; final `selftest fail=0`

## Evidence

| item | value |
| --- | --- |
| run evidence | `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-163149` |
| input manifest | `workspace/private/builds/audio/v2688-acdb-defined-module-topology-replay-deploy-plan/deploy-plan.json` |
| live manifest | `workspace/private/builds/audio/v2689-acdb-defined-module-topology-live-replay/live-manifest.json` |
| all-set log | `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-163149/60_acdb-setcal-replay-start-wait-all-set.txt` |
| PCM probe log | `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-163149/61_tinyplay-low-amplitude-speaker-pilot.txt` |
| dmesg after failure | `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-163149/62_dmesg-after-setcal-playback-failure-before-reset.txt` |
| deallocate log | `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-163149/63_acdb-setcal-helper-deallocate-check.txt` |
| rollback log | `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-163149/78_rollback-v2321.txt` |

## SET sequence

The device verified every staged artifact hash before replay. The helper then emitted all expected SET markers in order:

| index | cal_type | role | result |
| --- | --- | --- | --- |
| 0 | 39 | `CORE_CUSTOM_TOPOLOGIES` | `A90_ACDB_SETCAL_SET_OK` |
| 1 | 10 | `ADM_CUSTOM_TOPOLOGY_DEFINED_MODULES_ONLY_0x10004000` | `A90_ACDB_SETCAL_SET_OK` |
| 2 | 14 | `ASM_CUSTOM_TOPOLOGY_DEFINED_MODULES_ONLY_0x10005000` | `A90_ACDB_SETCAL_SET_OK` |
| 3 | 24 | `AFE_CUSTOM_TOPOLOGY_PAYLOAD` | `A90_ACDB_SETCAL_SET_OK` |
| 4 | 13 | `APP_META_HEADER` | `A90_ACDB_SETCAL_SET_OK` |
| 5 | 9 | `AFE_TOPOLOGY_HEADER` | `A90_ACDB_SETCAL_SET_OK` |
| 6 | 11 | `AUDPROC_COMMON_PAYLOAD` | `A90_ACDB_SETCAL_SET_OK` |
| 7 | 12 | `VOL_HEADER_NO_PAYLOAD` | `A90_ACDB_SETCAL_SET_OK` |
| 8 | 15 | `ASM_STREAM_PAYLOAD` | `A90_ACDB_SETCAL_SET_OK` |
| 9 | 23 | `AFE_TOPOLOGY_ID_HEADER` | `A90_ACDB_SETCAL_SET_OK` |
| 10 | 16 | `AFE_COMMON_PAYLOAD` | `A90_ACDB_SETCAL_SET_OK` |
| 11 | 21 | `SPEAKER_VI_HEADER` | `A90_ACDB_SETCAL_SET_OK` |

## Failure marker

The PCM probe failed at card `0`, device `0`:

```text
A90_PCM_PROBE_START version=V2386 card=0 device=0 channels=2 rate=48000 bits=16 data_bytes=192000 period_size=1024 period_count=4
A90_PCM_PROBE_PCM_OPEN_ERROR card=0 device=0 pcm_error="cannot open device 0 for card 0: Cannot allocate memory"
pcm_hw_open: cannot open device '/dev/snd/pcmC0D0p'[exit 20]
```

The relevant kernel markers were:

```text
q6asm_callback: cmd = 0x10dbe returned error = 0x2
send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]
msm_pcm_open: Could not allocate memory
msm-pcm-dsp soc:qcom,msm-pcm: ASoC: can't open platform soc:qcom,msm-pcm: -12
SM8150 Media1: ASoC: failed to start FE -12
```

## Interpretation

V2689 falsifies the narrow V2687/V2688 hypothesis: removing undefined module IDs from the forged cal_type `10` and `14` topology records is not sufficient. The DSP still rejects `ASM_CMD_ADD_TOPOLOGIES` with `ADSP_EBADPARAM`.

This means the root cause is not merely the two undefined module IDs (`0x10001f30`, `0x10001f10`) in the V2684 cal_type `14` selected record. More core-derived guessing is now low-value. The next branch should return to ACDB request-tuple recovery or capture/reconstruct the real subsystem custom-topology SET records for cal_type `10`/`14` from the Android-good path, rather than synthesizing them from the core topology DB.

## Validation

- Rollback preflight confirmed V2321 and V2237 rollback image hashes before the live run.
- Resident preflight before replay: V2321 `status` ok and `selftest fail=0`.
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --run-live --v2636-manifest workspace/private/builds/audio/v2688-acdb-defined-module-topology-replay-deploy-plan/deploy-plan.json --manifest-path workspace/private/builds/audio/v2689-acdb-defined-module-topology-live-replay/live-manifest.json --report docs/reports/NATIVE_INIT_V2689_AUDIO_ACDB_DEFINED_MODULE_TOPOLOGY_LIVE_REPLAY_2026-06-18.md --write-report`
- Checked rollback to V2321 passed: local SHA, remote SHA, boot readback SHA, boot, version, and selftest all passed.
- Post-run explicit health check: V2321 `status` ok and `selftest fail=0`.
