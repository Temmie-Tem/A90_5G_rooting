# NATIVE_INIT V2600 — ACDB indirect buffer tap build

Date: 2026-06-16

## Scope

Host-only build unit after V2599. No Android handoff, ACDB execution, native replay `SET`, speaker write, or raw payload publication was performed.

## Decision

- decision: `v2600-acdb-indirect-buffer-tap-build-ready`
- ok: `True`
- build tag: `v2600-acdb-indirect-buffer-tap-build-only`
- artifact: `workspace/private/builds/audio/v2600-acdb-indirect-buffer-tap-build-only/bin/liba90_acdb_indirect_buffer_tap_v2600.so`
- artifact sha256: `a8afef2ebc8f64f6df041f5ed2b4b1808601ef5e3e24e222669c93f7b98fa746`

## Capture Contract

- The tap remains silent while unarmed: init-time `acdb_ioctl` calls only call the real symbol.
- The future helper must call `a90_arm_capture()` after `acdb_loader_init_v3` returns and before driving the target getter/send path.
- With V2600 compile flags, armed calls dump full `in_buf` records and scan the first 16 input words for bounded `{length,pointer}` candidate buffers.
- A successful target still requires `ret==0`, `out_len==4916`, and non-all-zero bytes; requested length alone is not success.
- Fake allocation remains opt-in through `A90_ACDB_FAKE_ALLOCATE=1`; no new `/dev/msm_audio_cal` open or ioctl is introduced by this tap.

## Source State

- required_ok: `True`
- prohibited_ok: `True`
- sources:
  - `workspace/public/src/android/acdb_payload_capture/libacdbtap_v2475.c`
  - `workspace/public/src/android/acdb_payload_capture/a90_ioctl_trace_preload_v2531.c`

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_indirect_buffer_tap_v2600.py tests/test_build_android_acdb_indirect_buffer_tap_v2600.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_build_android_acdb_indirect_buffer_tap_v2600`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_indirect_buffer_tap_v2600.py --build --write-report`
- `git diff --check`

## Next Unit

Use this artifact only in a separately gated Android-good live handoff. The live unit must pull raw bytes privately and classify per-call records by `{cmd, buffer, in_len, out_len, ret, sha256, all_zero}` before any replay-manifest use.
