# NATIVE_INIT V2678 — ACDB custom-topology replay live attempt blocked by helper cap

Date: 2026-06-18

## Scope

One self-authorized recoverable-envelope live run of the V2639 native ACDB SET-cal replay
runner using the V2677 custom-topology overlay manifest.

The run staged the V2677 17-file manifest and attempted to replay:

1. cal_type 39 CORE_CUSTOM_TOPOLOGIES basic payload,
2. V2675 custom topology cal_type 24,
3. V2675 custom topology cal_type 14,
4. the original V2636 per-device SET sequence.

No forbidden partition was touched. The only flash operations were the checked V2334 candidate
boot image and checked rollback to V2321.

## Result

- decision: `v2639-acdb-setcal-replay-live-blocked`
- public classification: `v2678-helper-entry-cap-blocked-before-final-set`
- run_dir_private: `workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-150826`
- invoke_dir_private: `workspace/private/runs/audio/v2678-invoke`
- source_manifest_private: `workspace/private/builds/audio/v2677-audio-acdb-custom-topology-replay-deploy-plan/deploy-plan.json`
- V2677 manifest staged file count: `17`
- replay entry count: `11`
- final expected SET marker: `A90_ACDB_SETCAL_SET_OK index=10`
- route apply: `13/13`
- route reset: `12/12`
- runtime cleanup: `ok`
- rollback_v2321: `ok`
- rollback_version_ok: `True`
- rollback_selftest_fail0: `True`

## Blocking Evidence

The runner did not reach the final SET marker because the V2635 helper exited during argument
parsing:

```text
A90_SETCAL_REPLAY_HELPER_EXITED_BEFORE_ALL_SET
invalid --exact-set: /cache/a90-acdb-setcal-replay-v2677/10-set-arg-cal21.bin
[exit 32]
```

All staged ACDB file SHA checks before that point were `OK`, including the two new custom-topology
records:

- `/cache/a90-acdb-setcal-replay-v2677/01-custom-set-arg-cal24.bin`
- `/cache/a90-acdb-setcal-replay-v2677/01-custom-payload-cal24.bin`
- `/cache/a90-acdb-setcal-replay-v2677/02-custom-set-arg-cal14.bin`
- `/cache/a90-acdb-setcal-replay-v2677/02-custom-payload-cal14.bin`

Source inspection after the run identifies the concrete cause:

- `workspace/public/src/native-init/helpers/a90_acdb_setcal_replay_scaffold_v2635.c` defines `A90_MAX_REPLAY_ENTRIES 10`.
- V2677 requires `11` replay entries: one `--basic-payload` plus ten `--exact-set` records.
- Therefore the last header-only cal_type 21 argument is rejected before any final SET marker can be emitted.

This is a helper-capacity blocker, not a DSP or ACDB payload result. The expanded custom-topology
replay did not get far enough to test whether cal_type 24/14 clears the previous DSP-side rejection.

## Safety / Rollback

The recoverable envelope held:

- checked V2334 candidate flash completed before the run;
- ADSP and `/dev/snd` materialization succeeded;
- V2321 rollback used `native_init_flash.py`;
- post-rollback version output contained `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`;
- post-rollback selftest reported `fail=0`.

## Next Unit

Patch and rebuild the replay helper capacity, then regenerate the deploy/live plan before rerunning:

- increase `A90_MAX_REPLAY_ENTRIES` in `a90_acdb_setcal_replay_scaffold_v2635.c` to cover the V2677 11-entry manifest with small headroom;
- update the helper gate/report/tests so the rebuilt helper advertises and validates the new cap;
- rebuild the private helper artifact;
- regenerate a V2679-compatible deploy manifest that references the rebuilt helper;
- rerun the live replay only after static validation and dry-run confirm final index `10`.

## Validation

- V2677 preflight dry-run reported `execution_contract_ok=True`, `safe_to_run_native_replay=True`, `entry_count=11`, `file_count=17`, `final_set_index=10`.
- Live run executed under `native_audio_acdb_setcal_replay_live_handoff_v2639.py --run-live`.
- `result.json` confirmed `rolled_back=True`, `rollback_version_ok=True`, and `rollback_selftest_fail0=True`.
- `git diff --check` before commit.
