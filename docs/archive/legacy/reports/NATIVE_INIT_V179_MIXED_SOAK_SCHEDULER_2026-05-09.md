# A90 v179 Mixed Soak Scheduler Foundation Report

Date: `2026-05-09`
Device build under test: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v179` host harness, not a native-init boot image
Plan: `docs/plans/NATIVE_INIT_V179_MIXED_SOAK_SCHEDULER_PLAN_2026-05-09.md`
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

Result: `PASS`

v179 adds `native_test_supervisor.py mixed-soak` and
`a90harness/scheduler.py`. The scheduler now generates deterministic workload
plans, records workload events, and runs the existing read-only observer
concurrently with workload execution. The device remains on native init v159.

## Implementation

- Added `scripts/revalidation/a90harness/scheduler.py`.
- Added `mixed-soak` CLI to `scripts/revalidation/native_test_supervisor.py`.
- Added schedule model fields: `phase`, `workload`, `start_sec`, `end_sec`,
  `resource_locks`, `seed`.
- Added output artifacts: `schedule.json`, `workload-events.jsonl`,
  `mixed-soak-result.json`, `observer.jsonl`, `manifest.json`, `summary.md`,
  `README.md`, `bundle-index.json`.
- Kept evidence output on the existing private/no-follow writer path.

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

Results:

- Python compile: `PASS`
- Markdown/diff whitespace: `PASS`
- CLI help includes `mixed-soak`: `PASS`

Dry-run:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --dry-run \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 179 \
  --run-dir tmp/soak/harness/v179-dry-run-20260509-044249
```

Result:

- `PASS dry-run`
- workloads: `3`
- seed: `179`
- evidence: `tmp/soak/harness/v179-dry-run-20260509-044249/`

Real-device smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 179 \
  --run-dir tmp/soak/harness/v179-smoke-20260509-044258
```

Result:

- `PASS`
- workloads: `3`
- workload pass: `1`
- skipped/blocked: `2`
- observer failures: `0`
- observer samples: `35`
- evidence: `tmp/soak/harness/v179-smoke-20260509-044258/`

Evidence checks:

- `schedule.json`: present
- `workload-events.jsonl`: present
- `observer.jsonl`: present
- same-seed schedule diff: `deterministic=PASS`
- evidence directories: `0700`
- evidence files: `0600`

## Notes

The smoke run intentionally blocked `ncm-tcp-preflight` and `storage-io` because
`--allow-ncm` was not supplied. That is expected for v179 and matches the safety
gate policy. `cpu-mem-thermal` ran successfully as the active workload while the
observer continued collecting read-only samples.

## Result

v179 is accepted as the scheduler foundation. v180 can now add richer CPU and
memory workload profiles on top of this scheduler.
