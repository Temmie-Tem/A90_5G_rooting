# NATIVE_INIT V2622 — ACDB Gate-2 VOL-status handoff

Date: 2026-06-16

## Scope

Host-only Gate-2 status handoff after V2621. This unit combines the V2619
AUDPROC/AFE payload-candidate manifest with the V2621 VOL-isolated live result.
It does not run the device, replay calibration, copy raw payload bytes to tracked
paths, or mark native replay ready.

## Result

- decision: `v2622-gate2-vol-status-ready`
- ok: `True`
- private_manifest: `workspace/private/runs/audio/v2621-acdb-vol-isolated-20260616-211611/v2622-acdb-gate2-vol-status-manifest.json`
- native_replay_ready: `False`
- source_gate2_manifest: `workspace/private/runs/audio/v2618-acdb-direct-matrix-20260616-203644/v2619-acdb-gate2-handoff-manifest.json`
- source_v2618_run_dir: `workspace/private/runs/audio/v2618-acdb-direct-matrix-20260616-203644`
- source_v2621_run_dir: `workspace/private/runs/audio/v2621-acdb-vol-isolated-20260616-211611`
- payload_candidate_count: `3`
- payload_verified_count: `3`
- audproc_candidate_count: `2`
- afe_candidate_count: `1`
- vol_candidate_count: `0`
- vol_direct_get_exhausted_for_current_tuple: `True`
- vol_status_source_decision: `v2621-vol-isolated-vol-sweep-no-payload-rollback-pass`
- vol_status_ret_values: `{'size': [-19], 'data': [-19]}`

## Payload Candidates

| order | category | cmd | seq | buffer | bytes | sha256 |
| --- | --- | --- | --- | --- | ---: | --- |
| 1 | `AUDPROC_COMMON_CANDIDATE` | `0x00013265` | `0x00000004` | `ind-ap-common` | 18084 | `d1df14cd31bfa6a72b09e9e5075b629a215f10bbdb8e928849b9e2927190895c` |
| 2 | `AUDPROC_STREAM_CANDIDATE` | `0x00013269` | `0x00000006` | `ind-ap-stream` | 28 | `999e3e7ae5713992a3e03c247dbd9ceee7069d85053f6192486eb6c236c15d50` |
| 3 | `AFE_COMMON_CANDIDATE` | `0x0001326f` | `0x00000009` | `ind-afe-common` | 1560 | `f995c6c2d52a41d2e9be7d40ed9179a5c8ba037e62fccd9a9747b16d890e4fc0` |

## VOL Status

- classification: `v2621-vol-isolated-vol-sweep-no-payload`
- helper_done: `True`
- vol_sweep_seen: `True`
- vol_size_case_count: `16`
- vol_data_case_count: `16`
- vol_size_ret_values: `[-19]`
- vol_data_ret_values: `[-19]`
- vol_payload_count: `0`
- real_audio_set_pass_through_count: `0`
- helper_rc: `0`
- helper_sigsegv: `False`

## Boundary

- This is **not** a replay manifest.
- Raw payload paths are present only in the private manifest.
- Native replay remains blocked until operator Gate-2 mapping confirms the candidate cal types and decides whether the VOL-negative result is acceptable or a new VOL route is required.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_vol_status_handoff_v2622.py tests/test_native_audio_acdb_gate2_vol_status_handoff_v2622.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_gate2_vol_status_handoff_v2622 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_vol_status_handoff_v2622.py --write-report`
- `git diff --check`
