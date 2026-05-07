# v148 Plan: Long Soak Correlation

Date: `2026-05-08`
Target: `A90 Linux init 0.9.48 (v148)` / `0.9.48 v148 LONG SOAK CORRELATION`
Baseline: `A90 Linux init 0.9.47 (v147)`

## Summary

v148 adds the host/device evidence correlation layer for long-soak runs.
The device recorder remains independent; the host now exports the device JSONL and checks it against host cmdv1 observation records.

## Scope

- Copy v147 into `init_v148.c` and `v148/*.inc.c` with version/changelog bump.
- Extend `native_long_soak.py` to export device recorder JSONL through the native shell after the run.
- Add `scripts/revalidation/native_long_soak_report.py`.
- Report host failures, host command latency, device sample count, stop event count, sequence continuity, monotonic device timestamps, and monotonic device uptime.
- Keep 24h/overnight soak as an operator-run workflow rather than blocking this implementation version.

## Validation

- Static ARM64 build.
- Real-device flash and `cmdv1 version/status` verify.
- Short host/device run with host JSONL, device JSONL, summary JSON, and correlation report.
- Integrated validation, quick soak, and local targeted security rescan.
