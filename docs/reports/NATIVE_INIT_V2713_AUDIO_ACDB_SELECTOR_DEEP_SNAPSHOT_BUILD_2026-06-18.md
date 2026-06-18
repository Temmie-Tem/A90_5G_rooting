# NATIVE_INIT V2713 — ACDB selector deep-snapshot build

Date: 2026-06-18

## Scope

Host-only build-only unit. No Android handoff, device flash, native replay,
real or fake `AUDIO_SET_CALIBRATION` call from the V2713 preinit path, mixer
write, PCM write, speaker playback, or raw ACDB payload publication occurred.
Private build artifacts stay under `workspace/private`.

## Decision

- decision: `v2713-acdb-selector-deep-snapshot-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2713-acdb-selector-deep-snapshot-build-only`
- helper: `workspace/private/builds/audio/v2713-acdb-selector-deep-snapshot-build-only/bin/a90_acdb_selector_deep_snapshot_exec_linked_v2713`
- helper_sha256: `c5dd12cc28e7ab991f4c7a0e3439b848fa540accdda06b2711d9a9f0c6329106`
- preload: `workspace/private/builds/audio/v2713-acdb-selector-deep-snapshot-build-only/bin/liba90_acdb_selector_deep_snapshot_combined_preload_v2713.so`
- preload_sha256: `29549d375094d36eb2f3e661c4834ec45eb4b8f8c1a384a999822bd182446101`

## Why This Unit

V2712 closed existing replay candidates and left the selected cal10/cal14 selector contract as the active frontier.
V2704 already captured successful large-buffer lower GETs, but its shallow block snapshot showed the visible selector words are identical across cal24/10/14.
V2713 therefore adds a bounded deep snapshot of loader-internal node/block words before each lower GET.

The V2702 finding still applies: `AcdbCmdGetAudioCOPPTopologyData` returns `-12` from the
insufficient output-buffer branch after comparing request `word0` with the
ACDB table required size. The V2703/V2713 path therefore stops treating cal_type `10` as
absent and prepares a larger own-process destination buffer for the lower
custom-topology GET commands.

## Capture Contract

- `word0`: force GET destination capacity to `65536` bytes
- `word1`: force GET destination pointer to an own-process buffer
- selector snapshot: dump `v2713_selector_deep_snapshot` rows with 16 node words and 32 block words for cal_type `24`, `10`, and `14`
- ACDB tap: dump lower ADM/ASM/AFE custom-topology indirect outputs after `ret==0`
- success: future live run needs all three selector snapshot rows plus `ret==0` non-all-zero indirect buffers for cal_type `10` and `14`
- boundary: raw bytes stay private; native replay remains parked until selected payloads are recovered

## Source Checks

- required_ok: `True`
- prohibited_ok: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True, 'no_undefined_common_topology': True, 'no_undefined_send_audio_cal_v5': True, 'no_helper_lower_runner_dependency': True, 'no_helper_arm_capture_dependency': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'mode_0600': True, 'does_not_export_pthread_mutex_lock': True, 'does_not_export_pthread_mutex_unlock': True, 'does_not_export_android_log_print': True, 'exports_phase_common_hook': True, 'exports_common_skip_hook': True, 'exports_lower_runner': True, 'soname_v2713': True, 'exports_common_hook': True}`

## Next Unit

A future live Android-good handoff can stage the V2713 helper/preload through
the existing V2693/V2490 engine, force `A90_ACDB_FAKE_ALLOCATE=1`, pull the
full private event/acdbtap output, roll back to V2321, and report only metadata
for selector words and lower custom-topology indirect buffers. Native replay remains blocked.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_selector_deep_snapshot_v2713.py tests/test_build_android_acdb_selector_deep_snapshot_v2713.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_selector_deep_snapshot_v2713 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_selector_deep_snapshot_v2713.py --build --write-report`
- `git diff --check`
