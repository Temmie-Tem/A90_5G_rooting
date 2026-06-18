# NATIVE_INIT V2717 — ACDB route-first common-topology SET capture build

Date: 2026-06-18

## Scope

Host-only build-only unit. No Android handoff, device flash, native replay, real
`AUDIO_SET_CALIBRATION`, mixer write, PCM write, or speaker playback occurred.
Raw ACDB bytes remain private-only.

## Decision

- `decision`: `v2717-acdb-route-first-common-setcal-capture-build-only`
- `ok`: `True`
- `build_root`: `workspace/private/builds/audio/v2717-acdb-route-first-common-setcal-capture-build-only`
- helper: `workspace/private/builds/audio/v2717-acdb-route-first-common-setcal-capture-build-only/bin/a90_acdb_route_first_common_setcal_capture_exec_linked_v2717`
- helper_sha256: `43fcbda6552a5f706c05e7200737a2250895169d939262f0e124faeb203d28af`
- preload: `workspace/private/builds/audio/v2717-acdb-route-first-common-setcal-capture-build-only/bin/liba90_acdb_route_first_common_setcal_capture_combined_preload_v2717.so`
- preload_sha256: `094b8665cde241825c7b08af993a8b6e76e33ea6fec10fa6c25169bfdf946dfc`

## Why This Unit

V2716 exhausted the existing real-HAL traces for cal_types `10`, `14`, and
`24`; V2715 showed the lower hidden selector state remained stale. The one
cheap public-order variant not yet tried is to establish the speaker route
selector with `send_audio_cal_v5()` first, then ask for common custom topology.
V2717 builds that route-first helper while reusing the V2659 init-short phase
hook and the V2630 fake-SET capture boundary.

## Capture Contract

- helper call order is `init_v3 -> arm -> send_audio_cal_v5 -> common_topology`.
- first/init common hook patches `acdb_loader_is_initialized` state and returns `0`.
- post-init common hook calls the real `acdb_loader_send_common_custom_topology()` once.
- nested real-common reentry logs `common_reentry_neutralized` and returns `0`.
- V2630 SET shim preserves exact `AUDIO_SET_CALIBRATION` arg bytes and same-process dma-buf payloads before fake success.
- future live success is byte-exact SET records for cal_types `10`, `14`, and `24`.

## Boundary

- no direct `/dev/msm_audio_cal` open by the helper or shim
- no real `AUDIO_SET_CALIBRATION` pass-through
- no native ACDB replay, route mixer write, PCM write, AudioTrack, or speaker playback
- no persistent Magisk install and no raw ACDB bytes in public paths

## Build Evidence

- source_required_ok: `True`
- source_prohibited_ok: `True`
- helper_compile_ok: `True`
- tap_compile_ok: `True`
- ioctl_compile_ok: `True`
- route_first_phase_common_compile_ok: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True, 'undefined_send_audio_cal_v5': True, 'undefined_or_weak_a90_arm_capture': True, 'undefined_common_topology': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'mode_0600': True, 'does_not_export_pthread_mutex_lock': True, 'does_not_export_pthread_mutex_unlock': True, 'does_not_export_android_log_print': True, 'soname_v2717': True, 'exports_phase_common_hook': True}`

## Next Unit

A live Android-good handoff can stage the V2717 helper/preload, run with
`A90_ACDB_FAKE_ALLOCATE=1`, pull `acdb-route-first-common-events.jsonl`,
`acdb-v2717-route-first-phase-common-events.jsonl`, `setcal-events.jsonl`,
and private `setcal-*` raw files, then rollback to V2321.
The live unit must stop after capture and classify before any replay.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_route_first_common_setcal_capture_v2717.py tests/test_build_android_acdb_route_first_common_setcal_capture_v2717.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_route_first_common_setcal_capture_v2717 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_route_first_common_setcal_capture_v2717.py --build --write-report`
- `git diff --check`
