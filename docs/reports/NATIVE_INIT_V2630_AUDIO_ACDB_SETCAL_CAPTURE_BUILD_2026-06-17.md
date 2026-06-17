# NATIVE_INIT V2630 — ACDB SET-calibration capture build

Date: 2026-06-17

## Scope

Host-only build-only unit. No Android handoff, device flash, native replay SET, mixer,
PCM, or speaker write was performed. Raw ACDB bytes remain private-only.

## Decision

- decision: `v2630-acdb-setcal-capture-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2630-acdb-setcal-capture-build-only`
- helper: `workspace/private/builds/audio/v2630-acdb-setcal-capture-build-only/bin/a90_acdb_setcal_capture_exec_linked_v2630`
- helper_sha256: `e9c06a6b8228cbfd3aea833ba390b3d1731f2f9c5eea360b19454dc110ecf6f5`
- preload: `workspace/private/builds/audio/v2630-acdb-setcal-capture-build-only/bin/liba90_acdb_setcal_capture_combined_preload_v2630.so`
- preload_sha256: `806cc371ad573a3c8995f1b97c628d93b3d66bfc169cff962db39c67db9cfd19`

## Why This Unit

V2628 proved the AFE topology gate query is useful state evidence but not a replay
payload. V2629 therefore selected the SET path itself: intercept the loader's
`AUDIO_SET_CALIBRATION` call, preserve the exact `arg[0:data_size]` bytes, and only
then fake success so the kernel SET ioctl is never reached in this measurement unit.

## Capture Contract

- reuses the V2613 helper/preinit/acdbtap stack and swaps only the ioctl shim
- `AUDIO_SET_CALIBRATION` is always fake-successed; allocate/deallocate remain fake under `A90_ACDB_FAKE_ALLOCATE=1`
- every SET row emits `setcal-events.jsonl` with parsed `data_size`, `cal_type`, `cal_size`, `mem_handle`, and SHA-256
- full SET arg bytes are dumped as private `setcal-arg-*` files capped at 4096 bytes
- if `cal_size>0 && mem_handle>=0`, the same-process dma-buf fd is mmap'd read-only and dumped capped at 262144 bytes
- `cal_size==0` or `mem_handle<0` is `header-only`, not a capture failure

## Boundary

- no `/dev/msm_audio_cal` open in the shim
- no extra ioctl issuance; unrelated ioctls pass through only as in V2531
- no real `AUDIO_SET_CALIBRATION` pass-through
- no native replay, mixer, PCM, AudioTrack, or speaker write

## Build Evidence

- source_required_ok: `True`
- source_prohibited_ok: `True`
- helper_compile_ok: `True`
- tap_compile_ok: `True`
- ioctl_compile_ok: `True`
- preinit_compile_ok: `True`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True, 'mode_0600': True, 'undefined_send_audio_cal_v5': True, 'undefined_or_weak_a90_arm_capture': True}`
- preload_checks: `{'exports_acdb_ioctl': True, 'exports_ioctl': True, 'exports_common_topology': True, 'exports_a90_arm_capture': True, 'undefined_dlsym': True, 'undefined_errno': True, 'mode_0600': True, 'does_not_export_pthread_mutex_lock': True, 'does_not_export_pthread_mutex_unlock': True, 'does_not_export_android_log_print': True, 'soname_v2630': True}`

## Next Unit

Run an Android-good own-process handoff with the V2630 helper/preload override. The run
should pull `ioctl-trace-events.jsonl`, `setcal-events.jsonl`, and private `setcal-*` raw
files. Operator Gate-2 verification decides which SET rows enter replay.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_setcal_capture_v2630.py tests/test_build_android_acdb_setcal_capture_v2630.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_setcal_capture_v2630 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_setcal_capture_v2630.py --build --write-report`
- `git diff --check`
