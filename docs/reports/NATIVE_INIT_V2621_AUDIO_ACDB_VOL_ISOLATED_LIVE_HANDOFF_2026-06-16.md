# NATIVE_INIT V2621 — ACDB VOL-isolated live handoff

Date: 2026-06-16

## Scope

Android own-process ACDB VOL-isolated handoff using the V2490 checked Android
boot/stage/pull/rollback engine and the V2620 helper/preload artifacts. This
is measurement-only: no native replay `SET`, no speaker write, and raw buffers
remain under `workspace/private`.

## Result

- decision: `v2621-vol-isolated-vol-sweep-no-payload-rollback-pass`
- ok: `True`
- rolled_back: `True`
- counts_toward_fails_twice: `False`
- operator_valuable: `True`
- partial_success: `True`
- out_dir: `workspace/private/runs/audio/v2621-acdb-vol-isolated-20260616-211611`
- classification: `v2621-vol-isolated-vol-sweep-no-payload`
- helper_done: `True`
- safe_prelude_seen: `True`
- vol_sweep_seen: `True`
- case_return_count: `34`
- vol_size_case_count: `16`
- vol_data_case_count: `16`
- vol_size_ret_values: `[-19]`
- vol_data_ret_values: `[-19]`
- vol_size_ret_failed_count: `16`
- vol_data_ret_failed_count: `16`
- vol_request_in_buffer_count: `32`
- vol_size_indirect_count: `16`
- vol_payload_count: `0`
- real_audio_set_pass_through_count: `0`
- base_classification: `acdbtap-full-outbuf-set-no-4916-before-helper-exit`
- helper_rc: `0`
- helper_sigsegv: `False`

## Artifact Selection

- helper: `workspace/private/builds/audio/v2620-acdb-vol-isolated-build-only/bin/a90_acdb_vol_isolated_exec_linked_v2620`
- helper_sha256: `682f7a1438d22728a248698cfd8f521e5e1152b3b80060f3ac3de0876617532a`
- preload: `workspace/private/builds/audio/v2620-acdb-vol-isolated-build-only/bin/liba90_acdb_vol_isolated_combined_preload_v2620.so`
- preload_sha256: `1b3393576583a069fa131c37e4ed0b604e8afa97c30058e1a927e0822b1de40f`

## Contract

- stages the V2620 helper/preload through the V2490 Android-good handoff engine;
- forces `A90_ACDB_FAKE_ALLOCATE=1`; any real audio-cal SET pass-through is a boundary violation;
- keeps `acdb_ioctl` capture silent before `init_v3` returns and helper calls `a90_arm_capture()`;
- skips the V2618 crash command `0x12eeb` and already-captured AFE/AUDPROC matrix;
- executes only safe prelude plus `0x1326d`/`0x1326e` VOL sweep once;
- pulls `/data/local/tmp/a90-acdb-ownget/` and `acdbtap/` privately; and
- classifies VOL success only from `ret==0` plus non-all-zero `ind-ap-gain` raw buffers.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_vol_isolated_live_handoff_v2621.py tests/test_native_audio_acdb_vol_isolated_live_handoff_v2621.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_vol_isolated_live_handoff_v2621 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_vol_isolated_live_handoff_v2621.py --dry-run --write-report`
- live run, if present: `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_vol_isolated_live_handoff_v2621.py --run-live --write-report`
- `git diff --check`
