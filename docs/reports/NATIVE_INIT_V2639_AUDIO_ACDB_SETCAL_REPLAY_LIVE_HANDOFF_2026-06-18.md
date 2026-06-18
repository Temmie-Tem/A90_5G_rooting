# NATIVE_INIT V2639 — ACDB SET-cal replay live handoff

Date: 2026-06-18

## Scope

Exact-gated checked live handoff for future native replay of the V2636
SET-cal manifest. Default validation is host-only; live mode refuses before
device action unless Gate-2 acceptance is recorded and the exact approval is supplied.

## Result

- decision: `v2639-setcal-replay-live-handoff-dry-run`
- execution_contract_ok: `True`
- safe_to_run_native_replay: `False`
- live_runner_implemented: `True`
- manifest_path: `workspace/private/builds/audio/v2639-audio-acdb-setcal-replay-live-handoff/manifest.json`

## Gate Blockers

- exact live approval phrase not supplied
- operator Gate-2 acceptance flag not supplied
- V2636 deployment manifest does not record operator Gate-2 acceptance

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py tests/test_native_audio_acdb_setcal_replay_live_handoff_v2639.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_setcal_replay_live_handoff_v2639 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --dry-run --write-report`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --run-live --approval <exact> --operator-gate2-accepted` refused before device action because the V2636 manifest does not record Gate-2 acceptance
- `git diff --check`
