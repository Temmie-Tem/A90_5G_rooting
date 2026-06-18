# NATIVE_INIT V2707 — subsystem topology replay entry-cap deploy plan

Date: 2026-06-18

## Scope

Host-only fix for the V2706 pre-ACDB block. V2706 proved the V2705
manifest staged the old V2635 helper artifact and the helper rejected
the expanded 12-entry replay argv before any ACDB ioctl ran.

This unit rewrites the deploy manifest to stage the V2679 entry-cap helper
artifact and validates that the declared replay entry count fits the helper
contract. No device action, flash, audio playback, or calibration ioctl ran.

## Result

- decision: `v2707-entrycap-deploy-plan-ready`
- ok: `True`
- native_replay_ready: `True`
- safe_to_run_native_replay: `True`
- private_manifest: `workspace/private/builds/audio/v2707-audio-acdb-subsystem-topology-entrycap-deploy-plan/deploy-plan.json`
- remote_dir: `/cache/a90-acdb-setcal-replay-v2707`

## Helper Contract

- helper_private_path: `workspace/private/builds/audio/v2679-acdb-setcal-helper-entry-cap/bin/a90_acdb_setcal_replay_execute_v2635`
- helper_sha256: `5da19e3127255702f7ef2389d7252b4edf30c59185792f30057aa36a2ca33d18`
- expected_helper_sha256: `5da19e3127255702f7ef2389d7252b4edf30c59185792f30057aa36a2ca33d18`
- helper_ok: `True`
- max_replay_entries: `16`
- declared_replay_entries: `12`
- entry_count_fits: `True`

## Replay Shape

- prepended basic payloads: cal_type 39 core, 24 AFE, 10 ADM, 14 ASM
- existing exact SET records remain in the captured order after those topology payloads
- final live replay remains delegated to the checked V2639 runner

## Gate Blockers

- none

## Next Unit

V2708 may rerun the V2639 live replay with this V2707 manifest. The
expected new frontier is the actual ACDB SET sequence and subsequent PCM
probe; if it fails before the final SET marker again, that is no longer
the V2706 helper artifact mismatch.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707.py tests/test_native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707.py --write-report`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --dry-run --v2636-manifest workspace/private/builds/audio/v2707-audio-acdb-subsystem-topology-entrycap-deploy-plan/deploy-plan.json --manifest-path /tmp/v2639-v2707-preflight-manifest.json`
- `git diff --check`
