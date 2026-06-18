# NATIVE_INIT V2706 — subsystem topology ACDB SET replay live attempt

Date: 2026-06-18

## Scope

Run the self-authorized native ACDB SET replay using the V2705 deploy manifest:

- prepend captured subsystem custom topology payloads before stream open:
  - cal_type 24 AFE custom topology
  - cal_type 10 ADM custom topology
  - cal_type 14 ASM custom topology
- then replay the existing ordered SET-layer records from the V2636/V2632 manifest.
- keep the existing safety envelope: one-shot replay, bounded low-amplitude PCM probe only if replay reaches the final SET marker, route reset, runtime cleanup, and rollback to V2321.

## Result

- decision: `v2639-acdb-setcal-replay-live-blocked`
- interpreted V2706 decision: `v2706-blocked-before-acdb-ioctl-helper-entry-cap-mismatch`
- device action: live flash to V2334 candidate, ADSP boot/materialize, artifact stage, route apply, replay helper launch, route reset, runtime cleanup, rollback to V2321
- ACDB SET ioctl replay reached: `no`
- PCM probe attempted: `no`
- rollback: `ok`
- rollback version: `v2321-usb-clean-identity-rodata`
- rollback selftest: `fail=0`

## Evidence

Private run directory:

- `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-191912`

Key public-safe observations:

- V2705 manifest staged 16 files successfully; all SHA-256 checks passed on device.
- The route controls were applied and then reset successfully.
- The replay helper exited before any final SET marker.
- Failure text from the helper launch step:
  - `A90_SETCAL_REPLAY_HELPER_EXITED_BEFORE_ALL_SET`
  - `invalid --exact-set: /cache/a90-acdb-setcal-replay-v2705/07-set-arg-cal16.bin:/cache/a90-acdb-setcal-replay-v2705/07-payload-cal16.bin`
- This is the 11th replay entry in the V2705 argv sequence. The current source has `A90_MAX_REPLAY_ENTRIES 16`, but the V2705 deploy manifest still points at the older private V2635 helper artifact:
  - private helper SHA: `376f93488514467a40b7af4c3842004d553cf73fade90a2aef1aaa8e29e4da05`
- A newer private entry-cap helper artifact already exists and has a different SHA:
  - private V2679 helper SHA: `5da19e3127255702f7ef2389d7252b4edf30c59185792f30057aa36a2ca33d18`

## Interpretation

This run did not test the DSP-side custom-topology hypothesis. It failed before ACDB replay because the staged helper rejected the expanded 12-entry argv.

The strongest cause is a deploy-manifest/helper artifact mismatch: V2705 correctly generated a 12-entry replay sequence, but still reused the older V2635 private helper build that rejects the sequence at entry 11. The source tree already contains the expanded entry-cap implementation, and the private V2679 artifact appears to be the intended replacement.

## Next Unit

V2707 should be host-only:

1. update the deploy-plan builder to select the entry-cap helper artifact, or rebuild the helper from current source;
2. make the helper SHA/version explicit in the V2707 manifest;
3. add a gate that rejects any deploy manifest whose helper cannot accept at least the declared `replay_entries` count;
4. dry-run V2639 compatibility with the corrected manifest.

Only after V2707 passes should the live replay be rerun. This is not a DSP/ACDB negative result.

## Validation

- rollback image SHA checks passed before live execution.
- preflight `selftest verbose`: `fail=0`.
- V2639 dry-run with V2705 manifest: `execution_contract_ok=True`, `safe_to_run_native_replay=True`, `replay_gate_blockers=[]`.
- live run completed cleanup and rollback.
- final V2321 selftest: `fail=0`.
- `git diff --check`: passed.
