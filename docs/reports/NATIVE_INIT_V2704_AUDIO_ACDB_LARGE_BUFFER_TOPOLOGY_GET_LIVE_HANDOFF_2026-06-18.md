# NATIVE_INIT V2704 — ACDB large-buffer topology GET live handoff

Date: 2026-06-18

## Scope

Android own-process ACDB lower custom-topology GET capture using the V2490 checked Android
boot/stage/pull/rollback engine and the V2703 helper/preload artifacts. This is
measurement-only: no native replay, no speaker write, no real kernel SET from the V2703
preinit path, and raw buffers remain under `workspace/private`.

## Result

- decision: `v2704-large-buffer-lower-custom-topology-captured-rollback-pass`
- ok: `True`
- rolled_back: `True`
- counts_toward_fails_twice: `False`
- operator_valuable: `True`
- partial_success: `False`
- success: `True`
- out_dir: `workspace/private/runs/audio/v2704-acdb-large-buffer-topology-get-20260618-190151`
- rollback_health: `v2321 version verified; selftest fail=0`
- classification: `v2704-large-buffer-lower-custom-topology-captured`
- lower_stage_count: `0`
- lower_stages: `[]`
- lower_codes_by_stage: `{}`
- lower_values_by_stage: `{}`
- lower_cal_types_by_stage: `{}`
- acdbtap_row_count: `9`
- target_seen_count: `3`
- target_success_by_cal_type: `{'10': True, '14': True, '24': True}`
- captured_cal_types: `[10, 14, 24]`
- missing_cal_types: `[]`
- real_audio_set_pass_through_count: `0`

## Target Rows (metadata only)

| cal_type | seq | cmd | ret | out_len | buffer | raw_ok | sha256 |
| ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| 24 | 1 | `0x000130da` | 0 | 1180 | `ind-lower-afe-custom-topology` | `True` | `53307305946f1a39e1d57de10c5bb7d65d120ea8f1c90725d0432b684c8e92c4` |
| 10 | 2 | `0x00011394` | 0 | 16076 | `ind-lower-adm-custom-topology` | `True` | `fef3ed8df47486a54e625d632961f93366807f70413b47e08b35e7d00216ca36` |
| 14 | 3 | `0x00012e01` | 0 | 2356 | `ind-lower-asm-custom-topology` | `True` | `bc03e4be2dc4667ebfaf14b27ecc088f28fb23f784b352c14f0524963f7b7c98` |

Raw buffers are private. Public output reports only command, length, return code, and SHA-256.
A success classification requires cal_types `10`, `14`, and `24` to each have a
ret==0 non-zero indirect raw buffer with matching length and SHA.

## Artifact Selection

- helper: `workspace/private/builds/audio/v2703-acdb-large-buffer-topology-get-build-only/bin/a90_acdb_large_buffer_topology_get_exec_linked_v2703`
- helper_sha256: `c5dd12cc28e7ab991f4c7a0e3439b848fa540accdda06b2711d9a9f0c6329106`
- preload: `workspace/private/builds/audio/v2703-acdb-large-buffer-topology-get-build-only/bin/liba90_acdb_large_buffer_topology_get_combined_preload_v2703.so`
- preload_sha256: `5afa34ab09e8e87cfa4815c0c4a0058bd0d15539cfadac7774f6c48240ab5514`

## Contract

- stages the V2703 helper/preload through the V2490 Android-good handoff engine;
- forces `A90_ACDB_FAKE_ALLOCATE=1`; the V2703 preinit path does not call real or fake SET;
- uses the common-topology hook to patch initialized state, arm capture, run lower hidden nodes,
  and issue large-buffer GET commands for 24/10/14;
- captures lower ADM/ASM/AFE custom topology indirect outputs through `acdbtap`;
- pulls `/data/local/tmp/a90-acdb-ownget/` privately; and
- keeps native replay blocked until selected raw bytes are recovered and reviewed.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py tests/test_native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_large_buffer_topology_get_live_handoff_v2704 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py --dry-run --write-report`
- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_large_buffer_topology_get_live_handoff_v2704.py --run-live --write-report`
- if live run is present, post-live rollback must verify `a90ctl.py version` reports V2321 and
  `a90ctl.py selftest verbose` reports `fail=0`
- `git diff --check`
