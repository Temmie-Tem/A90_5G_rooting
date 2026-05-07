# Native Init v152 Power/Thermal Trend Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.52 (v152)` / `0.9.52 v152 POWER THERMAL TREND`
Baseline: `A90 Linux init 0.9.51 (v151)`

## Summary

- Extended `native_long_soak_report.py` with trend analysis over device JSONL samples.
- Trend JSON/Markdown now summarizes first, last, min, max, delta, average, and count for battery, power, thermal, memory, load, and uptime fields.
- The device recorder JSONL format remains backward-compatible.
- v151 bundle now carries the trend-enriched correlation report by default under v152 paths.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v152` | `e7b118beef5a0316e8bb79adaf763b3942e9966a9b4f122b99025c4316e0616c` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v152.cpio` | `8db7439c750458bad9f3aa43b725eef0e4a22057b67931aab7a96c4f277ae4cb` |
| `stage3/boot_linux_v152.img` | `01928ddf71bc3ebb39a450df6b88698e962b458e1e4bcb058a636947c688c854` |

## Validation

- Static ARM64 build for `init_v152` — PASS.
- Boot image marker checks for `A90 Linux init 0.9.52 (v152)`, `A90v152`, and `0.9.52 v152 POWER THERMAL TREND` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=15 failures=0`.
- `native_long_soak_report.py` — `PASS host_events=15 device_samples=6`.
- Trend check — PASS for `cpu_temp_c`, `gpu_temp_c`, `battery_pct`, `power_w`, `mem_used_mb`, and `load1` with 6 samples each.
- `native_disconnect_classify.py` — classification `serial-ok-ncm-down-or-inactive`, version match true.
- `native_long_soak_bundle.py` — `PASS bundle=tmp/soak/native-long-soak-v152-bundle missing=0 failed_commands=0`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Trend Snapshot

- `battery_pct`: first=100.0 last=100.0 delta=0.0 min=100.0 max=100.0 count=6.
- `power_w`: first=0.0 last=0.0 delta=0.0 min=0.0 max=0.0 count=6.
- `cpu_temp_c`: first=31.6 last=31.6 delta=0.0 min=31.6 max=31.6 count=6.
- `gpu_temp_c`: first=32.4 last=32.8 delta=0.4 min=32.4 max=32.8 count=6.
- `mem_used_mb`: first=252.0 last=252.0 delta=0.0 min=252.0 max=252.0 count=6.
- `load1`: first=0.57 last=0.79 delta=0.22 min=0.57 max=0.79 count=6.

## Notes

- The short 10-second run only validates trend extraction, not thermal stability.
- For an 8-hour or 24-hour run, reuse the v152 host JSONL/report/bundle flow and compare trend deltas before moving toward broader Wi-Fi/network exposure.
