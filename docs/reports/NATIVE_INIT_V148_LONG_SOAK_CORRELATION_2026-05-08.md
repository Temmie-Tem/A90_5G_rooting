# Native Init v148 Long Soak Correlation Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.48 (v148)` / `0.9.48 v148 LONG SOAK CORRELATION`
Baseline: `A90 Linux init 0.9.47 (v147)`

## Summary

- Extended `native_long_soak.py` to export device recorder JSONL into a host-side file.
- Added `native_long_soak_report.py` for host/device correlation checks.
- The report verifies host command failures, command latency, device sample count, recorder stop event, sequence continuity, monotonic device timestamps, and monotonic device uptime.
- Real-device flash, short correlation run, integrated validation, quick soak, and local security scan passed.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v148` | `aea811c768649bba7bf12e8e487c226fb3f08bf542921556605b7a3eb301b1c9` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v148.cpio` | `e1512b73bbcdafa0824bdc37ba69f7ea5d26656b309721b984b84f3c2d0ebf02` |
| `stage3/boot_linux_v148.img` | `663e9a84256216a4fe60a3bf9c4f042f3b790a6c0f8e221b188f3b3c13a85868` |

## Validation

- Static ARM64 build for `init_v148` and `a90_longsoak` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=12 failures=0`.
- `native_long_soak_report.py` — `PASS host_events=12 device_samples=6`.
- Correlation JSON: `host_failures=0`, `device_events=8`, `device_samples=6`, `device_stop_events=1`, `device_seq_contiguous=true`, `device_ts_monotonic=true`, `device_uptime_monotonic=true`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- v148 establishes the evidence format for overnight and workday soaks.
- A future long soak run should reuse the same host/device JSONL plus report flow with longer duration and less aggressive sampling.
