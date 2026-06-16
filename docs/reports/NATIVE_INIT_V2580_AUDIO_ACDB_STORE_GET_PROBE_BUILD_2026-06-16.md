# NATIVE_INIT V2580 — ACDB store-get pure-read harness build

## Scope

Host-only build-only unit after V2579. No device action, Android handoff, native calibration
ioctl, ACDB command execution, speaker write, or raw payload capture was performed.

## Decision

- decision: `v2580-acdb-store-get-probe-build-only`
- ok: `True`
- build_root: `workspace/private/builds/audio/v2580-acdb-store-get-probe-build-only`
- artifact: `workspace/private/builds/audio/v2580-acdb-store-get-probe-build-only/bin/a90_acdb_store_get_probe_exec_linked_v2580`
- artifact_sha256: `365137f08502ba03b02c03bd0f4f56f299589f6c81e703a74a71d17308ed0c39`
- source_required_ok: `True`
- source_prohibited_ok: `True`
- vendor_required_for_v2580: `{'has_acdb_loader_init_v3': True, 'has_acdb_loader_store_get_audio_cal': True}`

## Harness Contract

- Runtime is protected by `V2580_STORE_GET_GO`; without that marker, the binary exits before
  `acdb_loader_init_v3()` or `acdb_loader_store_get_audio_cal()`.
- The helper covers the five V2579 store-get cases: selector 37, selector 0 without/with
  instance data, and selector 1 without/with instance data.
- Output is bounded to 65536 bytes and metadata checks include `ret`, returned length,
  `all_zero`, and FNV-1a32. This preserves the V2530 rule: requested length alone is never
  success.
- The helper does not call direct `acdb_ioctl`, does not open `/dev/msm_audio_cal`, and does not
  contain native speaker playback code.

## Artifact Checks

- file: `ELF 32-bit LSB shared object, ARM, EABI5 version 1 (SYSV), dynamically linked, interpreter /system/bin/linker, not stripped`
- mode: `0o600`
- checks: `{'is_pie': True, 'entry_start': True, 'needed_ok': True, 'undefined_init_v3': True, 'undefined_store_get': True, 'no_undefined_acdb_ioctl': True, 'interpreter_system_linker': True, 'mode_0600': True}`

## Next Unit

V2581 should remain non-live unless a stricter future gate is written: add a dry-run/live runner
that refuses to execute without the marker file, stages this private helper plus the existing
fake-allocation preload, and classifies only metadata results. Actual native replay SET and
speaker playback remain blocked.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_store_get_probe_v2580.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_store_get_probe_v2580`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_store_get_probe_v2580.py --build --write-report`
- `git diff --check`
