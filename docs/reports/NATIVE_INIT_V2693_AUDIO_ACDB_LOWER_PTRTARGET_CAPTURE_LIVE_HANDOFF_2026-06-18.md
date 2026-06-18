# NATIVE_INIT V2693 — ACDB lower pointer-target capture live handoff

Date: 2026-06-18

## Scope

Android own-process ACDB pointer-target capture using the V2490 checked Android
boot/stage/pull/rollback engine and the V2692 helper/preload artifacts. This is
measurement-only: the SET shim fake-successes `AUDIO_SET_CALIBRATION`, no native replay
runs, no speaker write occurs, and raw pointer-target bytes remain private.

## Result

- decision: `v2693-ptrtarget-status-only-rollback-pass`
- ok: `True`
- rolled_back: `True`
- counts_toward_fails_twice: `False`
- operator_valuable: `True`
- partial_success: `True`
- success: `False`
- out_dir: `workspace/private/runs/audio/v2693-acdb-lower-ptrtarget-capture-20260618-171518`
- rollback_health: `v2321 version verified; selftest fail=0`
- classification: `v2693-ptrtarget-status-only`
- ptrtarget_status_count: `3`
- ptrtarget_dump_count: `0`
- ptrtarget_maps_verified_cal_types: `[]`
- ptrtarget_dumped_cal_types: `[]`
- missing_target_cal_types: `[10, 14, 24]`
- block_snapshot_count: `3`
- block_snapshot_cal_types: `[10, 14, 24]`

## Pointer Target Records (metadata only)

| seq | cal_type | cmd | requested_len | dump_len | status | raw_ok | raw_len | raw_sha256 |
| ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| - | - | - | - | - | - | - | - | - |

Raw `ptrtarget-pre` bytes are not committed. Public output records only length, status, and SHA-256.

## Pointer Target Status

V2692 block snapshots fired for all target lower custom-topology cal types. Each block
reported a `get_arg1` candidate pointer, but the in-process `/proc/self/maps` check rejected
all three candidates before any raw copy was attempted.

| cal_type | cmd | requested_len | mem_handle | ptrtarget_status | raw_dump |
| ---: | --- | ---: | ---: | --- | --- |
| 24 | `0x000130da` | 4096 | 35 | `ptrtarget_unmapped` | no |
| 10 | `0x00011394` | 4096 | 36 | `ptrtarget_unmapped` | no |
| 14 | `0x00012e01` | 4096 | 37 | `ptrtarget_unmapped` | no |

This is a partial-success / operator-valuable run: the lower-node block snapshot path is
confirmed for cal types 10/14/24, but the specific pointer target is not a valid same-process
mapping at the capture point.

## Artifact Selection

- helper: `workspace/private/builds/audio/v2692-acdb-lower-ptrtarget-capture-build-only/bin/a90_acdb_lower_ptrtarget_capture_exec_linked_v2692`
- helper_sha256: `c5dd12cc28e7ab991f4c7a0e3439b848fa540accdda06b2711d9a9f0c6329106`
- preload: `workspace/private/builds/audio/v2692-acdb-lower-ptrtarget-capture-build-only/bin/liba90_acdb_lower_ptrtarget_capture_combined_preload_v2692.so`
- preload_sha256: `ef240ffd236e65d21564069b37cb2ce472cdbdb03b8ff06b1c7c4eebb42acea4`

## Contract

- stages the V2692 helper/preload through the V2490 Android-good handoff engine;
- forces `A90_ACDB_FAKE_ALLOCATE=1`; the SET shim always fake-successes and any real
  kernel `AUDIO_SET_CALIBRATION` pass-through is a boundary violation;
- emits `v2692_lower_block_snapshot` before each lower hidden-node GET;
- emits `ptrtarget_status` and private `ptrtarget-pre` raw dumps only after `/proc/self/maps`
  verifies the requested same-process pointer range;
- pulls `/data/local/tmp/a90-acdb-ownget/` and nested `acdbtap/` privately; and
- classifies success when at least one target cal_type pointer target is dumped with valid raw SHA.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_lower_ptrtarget_capture_live_handoff_v2693.py tests/test_native_audio_acdb_lower_ptrtarget_capture_live_handoff_v2693.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_lower_ptrtarget_capture_live_handoff_v2693 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_lower_ptrtarget_capture_live_handoff_v2693.py --dry-run --write-report`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest discover tests -v`
- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_lower_ptrtarget_capture_live_handoff_v2693.py --run-live --write-report`
- if live run is present, post-live rollback must verify `a90ctl.py version` reports `0.9.285` / `v2321-usb-clean-identity-rodata` and `a90ctl.py selftest verbose` reports `fail=0`
- `git diff --check`
