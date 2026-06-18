# NATIVE_INIT V2672 — ACDB lower hidden-node SET capture build

Date: 2026-06-18

## Scope

Host-only build-only unit. No Android handoff, device flash, native replay, real
`AUDIO_SET_CALIBRATION`, mixer write, PCM write, speaker playback, or raw ACDB
payload publication occurred. Private build artifacts stay under `workspace/private`.

## Decision

- decision: `v2672-acdb-lower-hidden-node-setcal-capture-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2672-acdb-lower-hidden-node-setcal-capture-build-only`
- helper: `workspace/private/builds/audio/v2672-acdb-lower-hidden-node-setcal-capture-build-only/bin/a90_acdb_lower_hidden_node_setcal_capture_exec_linked_v2672`
- helper_sha256: `a32a4cc614ef461b3885477fbe5819fdb2075ceb7e628d116a4e9ccd533bfc69`
- preload: `workspace/private/builds/audio/v2672-acdb-lower-hidden-node-setcal-capture-build-only/bin/liba90_acdb_lower_hidden_node_setcal_capture_combined_preload_v2672.so`
- preload_sha256: `45497a843731a1621caa9912b5772b8ae08eb0af05dc495c700cf046989a27ac`

## Why This Unit

V2670 proved the public common path runtime-skips the 24/10/14 subsystem custom
SETs. V2671 then proved the matching lower blocks exist but are interior blocks
inside `acdb_loader_send_common_custom_topology()` and must not be jumped into
directly. V2672 therefore builds the safer sequence from the same lower primitives:
create a cal node, allocate its block, issue the pinned GET, then fake-capture the
generated SET arg and dma-buf through the V2630 shim.

## Capture Contract

- helper call order: `init_v3 -> a90_arm_capture -> a90_run_lower_hidden_nodes`.
- preload keeps the init common hook safe: skip real common, patch initialized flag, return to init.
- lower runner resolves libacdbloader base from `acdb_loader_is_initialized`.
- lower runner calls `create_cal_node(base+0xfd45)` and `allocate_cal_block(base+0xfbbd)`.
- lower runner targets cal_types `24`, `10`, and `14` with GET cmds `0x130da`, `0x11394`, and `0x12e01`.
- lower runner calls `AUDIO_SET_CALIBRATION` only through the linked V2630 fake SET shim.

## Boundary

- no helper `/dev/msm_audio_cal` open and no helper ioctl
- no real `AUDIO_SET_CALIBRATION` pass-through
- no direct jump to `0x90ea`, `0x924a`, or `0x93f6` interior common blocks
- no native replay, mixer, PCM, AudioTrack, speaker write, or persistent Magisk install
- raw ACDB bytes remain private-only and are not committed

## Build Evidence

- source_required_ok: `True`
- source_prohibited_ok: `True`
- helper_compile_ok: `True`
- tap_compile_ok: `True`
- ioctl_compile_ok: `True`
- lower_preload_compile_ok: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True, 'undefined_or_weak_a90_arm_capture': True, 'no_undefined_common_topology': True, 'no_undefined_send_audio_cal_v5': True, 'weak_a90_run_lower_hidden_nodes': True, 'undefined_arm_capture': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'mode_0600': True, 'does_not_export_pthread_mutex_lock': True, 'does_not_export_pthread_mutex_unlock': True, 'does_not_export_android_log_print': True, 'exports_phase_common_hook': True, 'soname_v2672': True, 'exports_common_skip_hook': True, 'exports_lower_runner': True}`

## Next Unit

A bounded Android-good live handoff can stage the V2672 helper/preload, force
`A90_ACDB_FAKE_ALLOCATE=1`, pull `acdb-v2672-lower-hidden-events.jsonl`,
`setcal-events.jsonl`, and private `setcal-*` raw files, then rollback to V2321.
The live unit must classify any real kernel SET pass-through as a boundary violation.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_lower_hidden_node_setcal_capture_v2672.py tests/test_build_android_acdb_lower_hidden_node_setcal_capture_v2672.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_lower_hidden_node_setcal_capture_v2672 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_lower_hidden_node_setcal_capture_v2672.py --build --write-report`
- `git diff --check`
