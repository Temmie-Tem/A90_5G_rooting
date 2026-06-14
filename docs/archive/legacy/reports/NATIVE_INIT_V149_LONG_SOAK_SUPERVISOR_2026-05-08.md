# Native Init v149 Long Soak Supervisor Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.49 (v149)` / `0.9.49 v149 LONG SOAK SUPERVISOR`
Baseline: `A90 Linux init 0.9.48 (v148)`

## Summary

- Added longsoak recorder health classification: `stopped`, `warming`, `ok`, `stale`.
- Added stale-sample detection based on recorder interval and latest device sample age.
- Added `stale=` and `max_age=` fields to `longsoak status`.
- Added warn-only longsoak selftest coverage.
- Updated host longsoak harness defaults to v149 and made status parsing compatible with the health-prefixed line.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v149` | `3062437ba13b7893ddb9872e058d82e2a7d68b5e22a166c89dd6935d0d3e15d6` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v149.cpio` | `b67f372120afd2790f8a843c6ce275349a55ef148bef27488470ab48b5ca6500` |
| `stage3/boot_linux_v149.img` | `13ff9f002dfb354022cbc92d3c012aea1331b59b260ac619c72813f1d8022742` |

## Validation

- Static ARM64 build for `init_v149` — PASS.
- Boot image marker checks for `A90 Linux init 0.9.49 (v149)` and `A90v149` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `longsoak status verbose` shows `health=stopped`, `stale=no`, `max_age=185000ms` — PASS.
- `selftest verbose` includes `longsoak` entry and reports no selftest failure — PASS.
- `bootstatus` includes compact longsoak health summary — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=15 failures=0`.
- `native_long_soak_report.py` — `PASS host_events=15 device_samples=6`.
- Correlation JSON: `host_failures=0`, `device_events=8`, `device_samples=6`, `device_stop_events=1`, `device_seq_contiguous=true`, `device_ts_monotonic=true`, `device_uptime_monotonic=true`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- Stale longsoak is intentionally a warning. It should not block shell/HUD entry.
- v150 should classify host-side disconnects so device recorder health can be correlated with ACM/NCM/bridge failures.
