# A90 v182 Failure Classifier + Recovery Policy Plan

Date: `2026-05-09`
Device build baseline: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v182` host harness, not a native-init boot image
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

v182 adds failure classification for mixed-soak evidence. This is useful even
while v181 full NCM validation is pending, because the current blocked/deferred
states must be distinguishable from real device or workload failures.

## Scope

- Add `scripts/revalidation/a90harness/failure.py`.
- Classify workload events and observer failures.
- Attach `failure-classification.json` to every mixed-soak run.
- Add classification path and summary to `mixed-soak-result.json` and summary.
- Preserve partial bundle validity on operator interrupt.

## Classification Targets

- `policy-blocked`: safety gate denied a workload.
- `env-ncm-missing`: NCM workload was explicitly allowed but host NCM path is absent.
- `bridge-disconnect` / `serial-disconnect`: reset/refused bridge paths.
- `bridge-timeout`: timeout symptoms.
- `storage-mismatch`: memory/storage/hash mismatch symptoms.
- `device-command-failed`: non-ok device rc/status.
- `operator-interrupt`: interrupted run with finalized partial bundle.

## Acceptance

- Artificial blocked workload is recorded as `policy-blocked`.
- NCM-missing workload with `--allow-ncm` is recorded as `env-ncm-missing` and
  remains deferred, not a generic failure.
- Operator interrupt finalizes a valid bundle with `operator-interrupt` and last
  good observer sample.
- `failure-classification.json`, `manifest.json`, `summary.md`, and
  `bundle-index.json` exist after interrupted runs.
