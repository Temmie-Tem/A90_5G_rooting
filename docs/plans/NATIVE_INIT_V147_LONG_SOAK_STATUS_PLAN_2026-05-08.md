# v147 Plan: Long Soak Status

Date: `2026-05-08`
Target: `A90 Linux init 0.9.47 (v147)` / `0.9.47 v147 LONG SOAK STATUS`
Baseline: `A90 Linux init 0.9.46 (v146)`

## Summary

v147 keeps the v146 recorder model and improves control/status visibility.
The goal is to make long-soak state useful from shell, boot/status screens, and host transcripts before adding correlation reporting.

## Scope

- Copy v146 into `init_v147.c` and `v147/*.inc.c` with version/changelog bump.
- Add `struct a90_longsoak_status` and `a90_longsoak_summary()`.
- Parse current recorder JSONL for sample count, last event type, sequence, and age.
- Show longsoak summary in `status` and `bootstatus`.
- Add `longsoak status verbose`.
- Extend `native_long_soak.py` with `longsoak status verbose` sampling and summary JSON output.

## Validation

- Static ARM64 build.
- Real-device flash and `cmdv1 version/status` verify.
- Short host/device long-soak run with summary JSON.
- `status` and `bootstatus` longsoak summary checks.
- Integrated validation, quick soak, and local targeted security rescan.
