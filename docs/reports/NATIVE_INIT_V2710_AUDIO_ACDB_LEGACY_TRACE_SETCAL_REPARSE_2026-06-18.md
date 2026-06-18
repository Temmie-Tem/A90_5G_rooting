# NATIVE_INIT V2710 — Legacy ACDB trace SET-cal reparse

Date: 2026-06-18

## Scope

Host-only reparse of the existing V2461/V2466 Android-good `/dev/msm_audio_cal` ptrace JSONL captures. The parser decodes only the first 32 bytes of each ioctl argument as header metadata. It does not read dma-buf payloads, write raw bytes, run a device step, or issue any ioctl.

## Inputs

- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p3629.jsonl`
- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p4368.jsonl`
- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p4369.jsonl`
- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p6558-late.jsonl`
- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p6561-late.jsonl`
- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p799.jsonl`
- `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p913.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p11362.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p3652.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p4381.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p4607.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p6921.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p7248.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p7809.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p802.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8763-late.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8763.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8765-late.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8765.jsonl`
- `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p933.jsonl`

## Result

- Decision: `v2710-legacy-real-hal-traces-have-no-subsystem-topology-setcal`
- Parsed files: `20`
- Parsed `/dev/msm_audio_cal` entries: `144`
- Existing traces contain target cal_type 10/14/24 `AUDIO_SET_CALIBRATION`: `False`
- Existing traces contain target cal_type 10/14/24 allocations: `True`
- Existing traces contain core topology cal_type 39 SET: `True`
- Same traces can supply byte-exact 10/14/24 SET geometry: `False`

## Target Cal Types

| cal_type | role | allocate_count | set_count | allocate_mem_handles | set_cal_sizes |
| --- | --- | ---: | ---: | --- | --- |
| `10` | `ADM_CUST_TOPOLOGY` | `5` | `0` | `[19, 21]` | `[]` |
| `14` | `ASM_CUST_TOPOLOGY` | `5` | `0` | `[24, 26]` | `[]` |
| `24` | `AFE_CUST_TOPOLOGY` | `5` | `0` | `[29, 31]` | `[]` |

## Control Cal Types

| cal_type | role | allocate_count | set_count | set_cal_sizes |
| --- | --- | ---: | ---: | --- |
| `39` | `CORE_CUSTOM_TOPOLOGIES` | `10` | `5` | `[4916]` |
| `20` | `AFE_FB_SPKR_PROT` | `0` | `4` | `[0]` |

## Full Request/Cal-Type Counts

| request | cal_type | count |
| --- | ---: | ---: |
| `AUDIO_ALLOCATE_CALIBRATION` | `2` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `3` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `4` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `5` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `10` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `11` | `10` |
| `AUDIO_ALLOCATE_CALIBRATION` | `12` | `10` |
| `AUDIO_ALLOCATE_CALIBRATION` | `14` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `15` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `16` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `17` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `19` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `24` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `25` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `27` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `34` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `35` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `37` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `39` | `10` |
| `AUDIO_ALLOCATE_CALIBRATION` | `40` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `46` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `48` | `5` |
| `AUDIO_ALLOCATE_CALIBRATION` | `49` | `5` |
| `AUDIO_DEALLOCATE_CALIBRATION` | `39` | `5` |
| `AUDIO_SET_CALIBRATION` | `20` | `4` |
| `AUDIO_SET_CALIBRATION` | `39` | `5` |

## Interpretation

- The legacy traces do show the ACDB loader allocating handles for cal_types `10`, `14`, and `24`, so the subsystem custom-topology cal types were part of initialization state.
- The same traces do not contain any `AUDIO_SET_CALIBRATION` for cal_types `10`, `14`, or `24`; only cal_type `39` core custom topology appears as a large SET record, plus cal_type `20` speaker-protection headers in V2466.
- Therefore V2461/V2466 cannot provide the byte-exact subsystem custom-topology SET records needed after V2708. This host-only reparse exhausts the operator-proposed legacy-trace shortcut.
- Native replay remains parked until a new Android-good capture or source-backed reconstruction produces exact SET arg/payload geometry for cal_types `10`, `14`, and `24`.

## Next Requirements

- Do not replay the V2707/V2708 manifest unchanged.
- Do not spend another iteration reparsing V2461/V2466 for cal_type 10/14/24 SET; this audit exhausts that source.
- Next useful input is a byte-exact Android-good SET event for cal_type 10, 14, and 24, or a source-backed reconstruction that changes the replay contract.
