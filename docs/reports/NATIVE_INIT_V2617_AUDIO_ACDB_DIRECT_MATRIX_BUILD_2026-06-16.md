# NATIVE_INIT V2617 — ACDB direct matrix build

Date: 2026-06-16

## Scope

Host-only build-only unit after V2616. It builds a future Android-good own-process
helper/preload pair that calls the V2616-pinned direct ACDB GET geometry. No device
handoff, flash, native replay `SET`, speaker write, or ACDB command execution occurred.

## Decision

- decision: `v2617-acdb-direct-matrix-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2617-acdb-direct-matrix-build-only`
- helper: `workspace/private/builds/audio/v2617-acdb-direct-matrix-build-only/bin/a90_acdb_direct_matrix_exec_linked_v2617`
- helper_sha256: `1c6b1012b07cb1beab76364e131ac05f950c80066c8bc2458b0063ea6ed70fd9`
- preload: `workspace/private/builds/audio/v2617-acdb-direct-matrix-build-only/bin/liba90_acdb_direct_matrix_combined_preload_v2617.so`
- preload_sha256: `be03b56d8cc9f29c716155ebc9e35b34e84f09977a9bc6621ed5c870d45571e2`

## Contract

- initialize through `acdb_loader_init_v3` with the V2611 empty meta-list arg3.
- preinit hook skips common topology and patches the initialized flag, as in V2608/V2611.
- arm the V2613 indirect-layout `acdb_ioctl` tap only after init returns; init-time calls are passthrough only.
- call direct ACDB GET commands from V2616; do not call `send_audio_cal_v5`.
- sweep VOL gain steps `0..15` with `0x1326d`/`0x1326e` to test whether cal_type 12 exists for any bounded step.
- keep exit-on-first-4916 disabled because this is the per-device matrix route, not a topology-only capture.
- keep native replay blocked; this is capture infrastructure only.

## Matrix

- base_commands: `['0x1122e', '0x1122d', '0x13267', '0x13265', '0x13268', '0x13269', '0x130d8', '0x13271', '0x1326f', '0x12eeb']`
- vol_sweep: `{'commands': ['0x1326d', '0x1326e'], 'gain_steps': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]}`
- max_direct_calls: `42`

## Build Evidence

- source_required_ok: `True`
- source_prohibited_ok: `True`
- helper_compile_ok: `True`
- tap_compile_ok: `True`
- preinit_compile_ok: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True, 'undefined_or_weak_a90_arm_capture': True, 'undefined_acdb_ioctl': True, 'does_not_reference_send_audio_cal_v5': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'mode_0600': True, 'does_not_export_pthread_mutex_lock': True, 'does_not_export_pthread_mutex_unlock': True, 'does_not_export_android_log_print': True, 'soname_v2617': True}`

## Next Unit

A future live unit may run this helper under Android-good with `A90_ACDB_FAKE_ALLOCATE=1`
and the V2617 preload, then pull the complete private `acdbtap` directory. Native replay
remains blocked until any new payloads and the existing V2615/V2616 mapping are operator
verified.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_direct_matrix_v2617.py tests/test_build_android_acdb_direct_matrix_v2617.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_direct_matrix_v2617 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_direct_matrix_v2617.py --build --write-report`
- `git diff --check`
