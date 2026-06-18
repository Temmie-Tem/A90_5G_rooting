# NATIVE_INIT V2703 — ACDB large-buffer topology GET build

Date: 2026-06-18

## Scope

Host-only build-only unit. No Android handoff, device flash, native replay,
real or fake `AUDIO_SET_CALIBRATION` call from the V2703 preinit path, mixer
write, PCM write, speaker playback, or raw ACDB payload publication occurred.
Private build artifacts stay under `workspace/private`.

## Decision

- decision: `v2703-acdb-large-buffer-topology-get-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2703-acdb-large-buffer-topology-get-build-only`
- helper: `workspace/private/builds/audio/v2703-acdb-large-buffer-topology-get-build-only/bin/a90_acdb_large_buffer_topology_get_exec_linked_v2703`
- helper_sha256: `c5dd12cc28e7ab991f4c7a0e3439b848fa540accdda06b2711d9a9f0c6329106`
- preload: `workspace/private/builds/audio/v2703-acdb-large-buffer-topology-get-build-only/bin/liba90_acdb_large_buffer_topology_get_combined_preload_v2703.so`
- preload_sha256: `5afa34ab09e8e87cfa4815c0c4a0058bd0d15539cfadac7774f6c48240ab5514`

## Why This Unit

V2702 showed that `AcdbCmdGetAudioCOPPTopologyData` returns `-12` from the
insufficient output-buffer branch after comparing request `word0` with the
ACDB table required size. V2703 therefore stops treating cal_type `10` as
absent and prepares a larger own-process destination buffer for the lower
custom-topology GET commands.

## Capture Contract

- `word0`: force GET destination capacity to `65536` bytes
- `word1`: force GET destination pointer to an own-process buffer
- ACDB tap: dump lower ADM/ASM/AFE custom-topology indirect outputs after `ret==0`
- success: future live run needs `ret==0` and non-all-zero raw buffers for selected cal_type `10` and `14`
- boundary: raw bytes stay private; native replay remains parked until selected payloads are recovered

## Source Checks

- required_ok: `True`
- prohibited_ok: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True, 'no_undefined_common_topology': True, 'no_undefined_send_audio_cal_v5': True, 'no_helper_lower_runner_dependency': True, 'no_helper_arm_capture_dependency': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'mode_0600': True, 'does_not_export_pthread_mutex_lock': True, 'does_not_export_pthread_mutex_unlock': True, 'does_not_export_android_log_print': True, 'exports_phase_common_hook': True, 'exports_common_skip_hook': True, 'exports_lower_runner': True, 'soname_v2703': True, 'exports_common_hook': True}`

## Next Unit

A future live Android-good handoff can stage the V2703 helper/preload through
the existing V2693/V2490 engine, force `A90_ACDB_FAKE_ALLOCATE=1`, pull the
full private `acdbtap` output, roll back to V2321, and report only metadata
for lower custom-topology indirect buffers. Native replay remains blocked.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_large_buffer_topology_get_v2703.py tests/test_build_android_acdb_large_buffer_topology_get_v2703.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_large_buffer_topology_get_v2703 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_large_buffer_topology_get_v2703.py --build --write-report`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest discover -s tests -v` (`1851` tests)
- `git diff --check`
