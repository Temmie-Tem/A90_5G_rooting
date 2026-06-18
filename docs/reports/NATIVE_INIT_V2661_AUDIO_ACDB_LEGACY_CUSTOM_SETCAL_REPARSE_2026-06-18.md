# NATIVE_INIT V2661 — ACDB legacy custom SETCAL reparse

Date: 2026-06-18

## Scope

Host-only reparse of existing private ACDB capture traces for the missing
custom-topology `AUDIO_SET_CALIBRATION` records. No Android boot, device
flash, native replay, real `/dev/msm_audio_cal` ioctl, mixer write, PCM
write, speaker playback, or raw ACDB publication occurred. This report is metadata only.

## Decision

- decision: `v2661-existing-traces-no-custom-setcal-host-only`
- ok: `True`
- target_cal_types: `[10, 14, 24]`
- target_set_cal_types: `[]`
- missing_target_set_cal_types: `[10, 14, 24]`
- target_allocate_cal_types: `[10, 14, 24]`

## Run Summaries

| run | records | requests | allocated targets | SET cal types | target SETs |
| --- | ---: | --- | --- | --- | --- |
| `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530` | `28` | `{'AUDIO_ALLOCATE_CALIBRATION': 26, 'AUDIO_DEALLOCATE_CALIBRATION': 1, 'AUDIO_SET_CALIBRATION': 1}` | `[10, 14, 24]` | `[39]` | `[]` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643` | `116` | `{'AUDIO_ALLOCATE_CALIBRATION': 104, 'AUDIO_DEALLOCATE_CALIBRATION': 4, 'AUDIO_SET_CALIBRATION': 8}` | `[10, 14, 24]` | `[20, 39]` | `[]` |
| `workspace/private/runs/audio/v2660-acdb-custom-topology-phase-common-setcal-capture-20260618-123009` | `25` | `{'AUDIO_ALLOCATE_CALIBRATION': 25}` | `[10, 14, 24]` | `[]` | `[]` |

## SET Records Observed

### `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530`

| source | seq | cal_type | cal_size | mem_handle |
| --- | ---: | ---: | ---: | ---: |
| `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-p4368.jsonl` | `28` | `39` `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` | `4916` | `37` |

### `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643`

| source | seq | cal_type | cal_size | mem_handle |
| --- | ---: | ---: | ---: | ---: |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p4381.jsonl` | `28` | `39` `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` | `4916` | `37` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p4381.jsonl` | `29` | `20` `CAL_TYPE_20` | `0` | `-1` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p4381.jsonl` | `30` | `20` `CAL_TYPE_20` | `0` | `-1` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p7248.jsonl` | `28` | `39` `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` | `4916` | `35` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p802.jsonl` | `28` | `39` `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` | `4916` | `37` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8763.jsonl` | `28` | `39` `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` | `4916` | `37` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8763.jsonl` | `29` | `20` `CAL_TYPE_20` | `0` | `-1` |
| `workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-p8763.jsonl` | `30` | `20` `CAL_TYPE_20` | `0` | `-1` |

### `workspace/private/runs/audio/v2660-acdb-custom-topology-phase-common-setcal-capture-20260618-123009`

No `AUDIO_SET_CALIBRATION` metadata records decoded.

## Interpretation

The existing Android-good traces do **not** contain byte-exact SET records
for cal_types `10`, `14`, or `24`. They do confirm the database/loader
allocates all three target custom-topology cal blocks, so the missing
evidence is a SET-path/control-flow problem, not absence from the ACDB DB.

V2660 adds the same conclusion from the own-process path: the phase-aware
init-short hook allowed `acdb_loader_init_v3()` to fake-allocate `10/14/24`,
but the process SIGSEGVed before the helper regained control and before any
post-init `AUDIO_SET_CALIBRATION` rows were emitted. Therefore V2659/V2660
should not be rerun unchanged.

## Next Unit

Proceed host-only to a lower-function/direct SET-path design. The immediate
candidates are the stock `libacdbloader.so` paths named by its own strings:
`send_adm_custom_topology`, `send_asm_custom_topology`, and
`send_afe_custom_topology`, or an exported lower SET helper if its argument
layout can be pinned. A future live run must remain measurement-only: fake
all `AUDIO_SET_CALIBRATION`, dump arg/payload bytes privately, and rollback
to V2321.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_legacy_custom_setcal_v2661.py tests/test_analyze_audio_acdb_legacy_custom_setcal_v2661.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests/test_analyze_audio_acdb_legacy_custom_setcal_v2661.py -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_legacy_custom_setcal_v2661.py --write-report`
- `git diff --check`
