# A90 v179 Mixed Soak Scheduler Foundation Plan

Date: `2026-05-09`
Device build baseline: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v179` host harness, not a native-init boot image
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

v179 adds the host-side mixed-soak scheduler foundation required before v180-v184
can run longer CPU, memory, NCM/TCP, storage, failure-classification, and
serverization readiness gates. This is not a device firmware bump; the live phone
continues to run native init v159.

## Scope

- Add `scripts/revalidation/a90harness/scheduler.py`.
- Add `native_test_supervisor.py mixed-soak`.
- Generate deterministic `schedule.json` from `seed`, `profile`, `workload`, and
  `duration-sec`.
- Run observer and workload execution concurrently through the existing
  single-writer `DeviceClient` lock.
- Record `workload-events.jsonl`, `observer.jsonl`, `mixed-soak-result.json`,
  `manifest.json`, `summary.md`, and bundle index files through private evidence
  writers.
- Treat safety-gated workloads as structured `blocked`/`skipped` events rather
  than generic failures.

## Non-Goals

- No native init source or boot image change.
- No Wi-Fi enablement, public listener widening, USB rebind, watchdog open, or
  destructive partition write.
- No full v180 CPU/memory profile matrix yet.
- No v181 NCM/TCP+storage one-hour requirement yet.

## Commands

Dry-run:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --dry-run \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 179
```

Smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 179
```

## Acceptance

- `mixed-soak` appears in supervisor CLI help.
- `schedule.json` contains phase, workload, start/end, resource locks, and seed.
- Same seed produces the same schedule.
- Observer runs while workload events are processed.
- Short real-device smoke PASS with observer failures `0`.
- Evidence directories are `0700`; evidence files are `0600`.
- NCM-gated workloads are blocked/skipped when `--allow-ncm` is absent.
- Next executable item becomes v180 CPU/Memory Workload Profiles.
