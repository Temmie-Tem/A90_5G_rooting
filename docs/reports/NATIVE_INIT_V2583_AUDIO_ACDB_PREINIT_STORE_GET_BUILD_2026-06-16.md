# NATIVE_INIT V2583 — ACDB pre-init store-get probe build

## Scope

Host-only build-only unit after V2582. No device action, Android handoff, native replay SET,
speaker write, or raw ACDB payload publication was performed.

## Decision

- decision: `v2583-acdb-preinit-store-get-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2583-acdb-preinit-store-get-build-only`
- helper: `workspace/private/builds/audio/v2583-acdb-preinit-store-get-build-only/bin/a90_acdb_preinit_store_get_exec_linked_v2583`
- helper_sha256: `f38d250243216b8ea300ac68f8720ad24c411dd406950ee48a24a29b6e9da6bc`
- preload: `workspace/private/builds/audio/v2583-acdb-preinit-store-get-build-only/bin/liba90_acdb_preinit_store_get_v2583.so`
- preload_sha256: `02b089b680dd01202d15a73a8e5913376b355039a4b7dbb685aab1a53fa07d09`
- source_required_ok: `True`
- source_prohibited_ok: `True`
- vendor_required_for_v2583: `{'has_acdb_loader_init_v3': True, 'has_acdb_loader_is_initialized': True, 'has_acdb_loader_send_common_custom_topology': True, 'has_acdb_loader_store_get_audio_cal': True}`

## Rationale

- V2582 proved the V2580 post-init store-get helper never reaches its cases: `init_v3()`
  itself enters common topology and then crashes before returning.
- Repeating a literal post-init arm/store-get path is therefore not useful for this binary.
- V2583 moves the same five V2580 store-get metadata cases into a common-topology hook, after
  the initialized flag patch and before the known init-tail crash.
- The real common-topology call is skipped because the topology payload is already pinned; this
  unit targets lower GET metadata only.

## Boundaries

- The helper only calls `acdb_loader_init_v3()`.
- The preload writes metadata only: `ret`, returned length, all-zero discriminator, and FNV-1a32.
- The helper/preinit source does not open `/dev/msm_audio_cal`, does not call `ioctl()`, and does
  not call direct `acdb_ioctl()`.
- The linked V2531 ioctl wrapper is present only for future fake-success ALLOC/DEALLOC/SET under
  `A90_ACDB_FAKE_ALLOCATE=1`; no real native replay is run in this unit.

## Artifact Checks

- helper_file: `ELF 32-bit LSB shared object, ARM, EABI5 version 1 (SYSV), dynamically linked, interpreter /system/bin/linker, not stripped`
- helper_checks: `{'is_pie': True, 'entry_start': True, 'undefined_init_v3': True, 'needed_libacdbloader': True, 'needed_libaudcal': True}`
- preload_file: `ELF 32-bit LSB shared object, ARM, EABI5 version 1 (SYSV), dynamically linked, not stripped`
- preload_checks: `{'exports_ioctl': True, 'exports_common_topology': True, 'does_not_export_acdb_ioctl': True, 'undefined_dlsym': True, 'undefined_errno': True, 'soname': True}`

## Next Unit

A future V2584 live runner can stage these private artifacts through the checked Android handoff,
set `A90_ACDB_FAKE_ALLOCATE=1`, and classify only the metadata rows. Native calibration SET and
speaker playback remain blocked until per-device payload bytes/order and cleanup policy are pinned.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_preinit_store_get_probe_v2583.py tests/test_build_android_acdb_preinit_store_get_probe_v2583.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_preinit_store_get_probe_v2583`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_preinit_store_get_probe_v2583.py --build --write-report`
- `git diff --check`
