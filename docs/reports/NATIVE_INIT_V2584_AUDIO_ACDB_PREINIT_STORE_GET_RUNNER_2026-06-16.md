# NATIVE_INIT V2584 — ACDB pre-init store-get runner

Date: 2026-06-16

## Scope

Host-only runner unit after V2583. No live Android handoff, native calibration SET, speaker write, or raw ACDB payload publication was performed in this iteration.

## Decision

- decision: `v2584-acdb-preinit-store-get-live-runner-dry-run`
- ok: `True`
- live_ready: `True`
- live_blockers: `[]`

## Runner Contract

- exact live gate: `AUD-ACDB-V2584-preinit-store-get go: one-shot preinit store_get metadata capture on Android, fake allocate preload, no SET replay, no speaker write, rollback to V2321`
- V2584 stages the V2583 preload through the V2490 ioctl-trace preload slot.
- The helper only enters `acdb_loader_init_v3()`; the pre-init hook runs the five V2580 store-get metadata cases before the known init-tail crash.
- Success requires `ret==0` plus `all_zero=false` in V2583 `case_return` metadata; requested length alone is not success.
- Native replay SET, speaker playback, and raw payload publication remain blocked.

## Artifacts

- helper_sha256: `f38d250243216b8ea300ac68f8720ad24c411dd406950ee48a24a29b6e9da6bc`
- preload_sha256: `02b089b680dd01202d15a73a8e5913376b355039a4b7dbb685aab1a53fa07d09`

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_preinit_store_get_live_handoff_v2584.py tests/test_native_audio_acdb_preinit_store_get_live_handoff_v2584.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_preinit_store_get_live_handoff_v2584`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_preinit_store_get_live_handoff_v2584.py --write-report`
- `git diff --check`
