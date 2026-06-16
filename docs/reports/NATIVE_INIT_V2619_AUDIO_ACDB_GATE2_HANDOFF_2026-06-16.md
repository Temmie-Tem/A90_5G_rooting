# NATIVE_INIT V2619 — ACDB Gate-2 handoff manifest

Date: 2026-06-16

## Scope

Host-only handoff of the V2618 ACDB direct-matrix capture. This unit does not
run the device, does not replay calibration, and does not copy raw payload bytes
into tracked paths. It writes a private raw-path manifest for operator Gate-2
mapping and a public redacted report with command/order/length/SHA metadata.

## Result

- decision: `v2619-gate2-handoff-ready`
- ok: `True`
- source_decision: `v2618-direct-matrix-perdevice-partial-no-vol-rollback-pass`
- source_rolled_back: `True`
- source_run_dir: `workspace/private/runs/audio/v2618-acdb-direct-matrix-20260616-203644`
- private_manifest: `workspace/private/runs/audio/v2618-acdb-direct-matrix-20260616-203644/v2619-acdb-gate2-handoff-manifest.json`
- native_replay_ready: `False`
- payload_candidate_count: `3`
- payload_verified_count: `3`
- audproc_candidate_count: `2`
- afe_candidate_count: `1`
- vol_candidate_count: `0`
- topology_candidate_count: `0`
- case_return_count: `9`
- vol_case_return_count: `0`
- real_audio_set_pass_through_count: `0`

## Payload Candidates

| order | category | cmd | seq | buffer | bytes | sha256 |
| --- | --- | --- | --- | --- | ---: | --- |
| 1 | `AUDPROC_COMMON_CANDIDATE` | `0x00013265` | `0x00000004` | `ind-ap-common` | 18084 | `d1df14cd31bfa6a72b09e9e5075b629a215f10bbdb8e928849b9e2927190895c` |
| 2 | `AUDPROC_STREAM_CANDIDATE` | `0x00013269` | `0x00000006` | `ind-ap-stream` | 28 | `999e3e7ae5713992a3e03c247dbd9ceee7069d85053f6192486eb6c236c15d50` |
| 3 | `AFE_COMMON_CANDIDATE` | `0x0001326f` | `0x00000009` | `ind-afe-common` | 1560 | `f995c6c2d52a41d2e9be7d40ed9179a5c8ba037e62fccd9a9747b16d890e4fc0` |

## Gate-2 Boundary

- These rows are **not** a replay manifest yet.
- Operator must verify size/order to cal_type mapping before any V2552 replay extension.
- VOL is still absent in V2618; replay remains blocked for the VOL cal_type path.
- Raw payload paths exist only in the private manifest and must not be committed.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_handoff_v2619.py tests/test_native_audio_acdb_gate2_handoff_v2619.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_gate2_handoff_v2619 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_handoff_v2619.py --write-report`
- `git diff --check`
