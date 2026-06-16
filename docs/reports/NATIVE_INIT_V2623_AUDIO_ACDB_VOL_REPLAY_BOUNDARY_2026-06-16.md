# NATIVE_INIT V2623 — ACDB VOL replay-boundary reconciliation

Date: 2026-06-16

## Scope

Host-only reconciliation of the VOL/per-device replay boundary after V2622.
This reads private metadata from V2461, V2612, V2618, V2621, and V2622,
but emits only public-safe counts, command IDs, lengths, and SHA-256 values.
No device action, raw payload copy, native replay, speaker write, or calibration ioctl runs here.

## Result

- decision: `v2623-vol-negative-boundary-pinned`
- ok: `True`
- native_replay_ready: `False`
- recommended_next_gate: `operator-gate2-decision-on-vol-negative-manifest`
- safe_to_run_native_replay_without_operator_gate2: `False`

## Android-good `/dev/msm_audio_cal` stream cross-check (V2461)

- source_dir: `workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530`
- decoded_ioctl_entries: `28`
- by_request: `{'0xc00461c8': 26, '0xc00461c9': 1, '0xc00461cb': 1}`
- allocate_count: `26`
- deallocate_count: `1`
- set_count: `1`
- set_cal_types: `[39]`
- allocated_required_cal_types: `[11, 12, 15, 16, 39]`
- android_set_payload_stream_has_vol: `False`
- android_set_payload_stream_has_audproc_or_afe: `False`

| seq | request | cal_type | name | buffer | cal_size | mem_handle |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| 28 | `AUDIO_SET_CALIBRATION` | 39 | `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` | 0 | 4916 | 37 |

## Own-process GET cross-check

| run | VOL out rows | VOL ret values | VOL payloads | note |
| --- | ---: | --- | ---: | --- |
| V2612 send_audio_cal_v5 | 2 | `[-19]` | 0 | first post-init send path; gain step 0 returned -19 |
| V2618 direct matrix | 0 | `[]` | 0 | captured AUDPROC/AFE candidates, no VOL candidate |
| V2621 VOL-isolated sweep | 32 | `[-19]` | 0 | 16 gain steps, size+data, all -19 |

## Current Gate-2 candidate set

- source: `workspace/private/runs/audio/v2621-acdb-vol-isolated-20260616-211611/v2622-acdb-gate2-vol-status-manifest.json`
- ok: `True`
- payload_candidate_count: `3`
- payload_verified_count: `3`
- audproc_candidate_count: `2`
- afe_candidate_count: `1`
- vol_candidate_count: `0`
- vol_direct_get_exhausted_for_current_tuple: `True`

| category | cmd | buffer | bytes | sha256 |
| --- | --- | --- | ---: | --- |
| `AUDPROC_COMMON_CANDIDATE` | `0x00013265` | `ind-ap-common` | 18084 | `d1df14cd31bfa6a72b09e9e5075b629a215f10bbdb8e928849b9e2927190895c` |
| `AUDPROC_STREAM_CANDIDATE` | `0x00013269` | `ind-ap-stream` | 28 | `999e3e7ae5713992a3e03c247dbd9ceee7069d85053f6192486eb6c236c15d50` |
| `AFE_COMMON_CANDIDATE` | `0x0001326f` | `ind-afe-common` | 1560 | `f995c6c2d52a41d2e9be7d40ed9179a5c8ba037e62fccd9a9747b16d890e4fc0` |

## Conclusion

- V2461 proves the captured Android-good `/dev/msm_audio_cal` SET payload stream contains the custom topology SET only (`cal_type=39`), while VOL (`cal_type=12`) appears only as allocation metadata in that stream.
- V2612 and V2621 independently show the current speaker tuple's VOL GET path returning `-19`; V2621 extends this through all 16 gain steps.
- The current replay candidate remains topology plus the three verified AUDPROC/AFE candidates. This may be enough to test the V2393 `pcm_prepare` blockers, but it is not authorized by this unit.
- Native replay remains blocked until operator Gate-2 explicitly accepts the VOL-negative manifest or provides a new VOL route.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_vol_replay_boundary_v2623.py tests/test_analyze_audio_acdb_vol_replay_boundary_v2623.py`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_vol_replay_boundary_v2623 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_vol_replay_boundary_v2623.py --write-report`
- `git diff --check`
