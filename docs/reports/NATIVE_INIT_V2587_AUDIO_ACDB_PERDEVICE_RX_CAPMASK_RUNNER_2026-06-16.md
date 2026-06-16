# NATIVE_INIT V2587 — ACDB per-device RX cap-mask runner

Date: 2026-06-16

## Scope

Host-only runner unit after V2586. No live Android handoff, native replay SET, speaker write,
or raw ACDB payload publication was performed in this iteration.

## Decision

- decision: `v2587-acdb-perdevice-rx-capmask-live-runner-dry-run`
- ok: `True`
- live_ready: `True`
- live_blockers: `[]`

## Runner Contract

- exact live gate: `AUD-ACDB-V2587-perdevice-rx-capmask go: one-shot send_audio_cal_v5 arg2=1 per-device capture on Android, fake allocate preload, no SET replay, no speaker write, rollback to V2321`
- stages the V2586 helper/preload artifacts where `send_audio_cal_v5` arg2 is `1`.
- reuses V2573 generic direct/indirect ACDB tap classification.
- forces `A90_ACDB_FAKE_ALLOCATE=1`; native replay SET and speaker playback remain blocked.
- success requires `ret==0` and non-all-zero raw payload; requested length alone is not success.

## Artifacts

- helper_sha256: `5cc7b9c6f2bacdb7c4789bb9f9f62ec2f2ec7488e9124e97b0364b3644af023d`
- preload_sha256: `f247bd9e2afa31ef872bf59d6a25d060947a7bfe364a41b2fec58956fdbe5107`

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_perdevice_rx_capmask_live_handoff_v2587.py tests/test_native_audio_acdb_perdevice_rx_capmask_live_handoff_v2587.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_perdevice_rx_capmask_live_handoff_v2587`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_perdevice_rx_capmask_live_handoff_v2587.py --build-v2586-artifacts --write-report`
- `git diff --check`
