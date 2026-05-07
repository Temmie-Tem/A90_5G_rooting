# Native Init v147 Long Soak Status Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.47 (v147)` / `0.9.47 v147 LONG SOAK STATUS`
Baseline: `A90 Linux init 0.9.46 (v146)`

## Summary

- Added `struct a90_longsoak_status` and `a90_longsoak_summary()`.
- `longsoak status` now reports running state, pid, interval, session, sample count, last event type, sequence, and age.
- `longsoak status verbose` prints status plus the last recorder JSONL entry.
- `status` and `bootstatus` now include the longsoak summary.
- `native_long_soak.py` now records `longsoak status verbose` and writes a summary JSON file.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v147` | `01b4f3009365a18bd9583fcf1c7a396e95b49c7b68d32bb29a4efe65cfa49fdb` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v147.cpio` | `eab528c4f0e66035c6f5a69d39f85c84373cdae767bc26acd4b5547f4cf353d7` |
| `stage3/boot_linux_v147.img` | `ca0a1772976b75262adc55659dac61c719a9da153beecda13f146182eea3532a` |

## Validation

- Static ARM64 build for `init_v147` and `a90_longsoak` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=9 failures=0`.
- `tmp/soak/native-long-soak-v147-summary.json` recorded `ok=9`, `failures=0`, `max_duration_sec=0.5026314299902879`.
- `status` showed `longsoak: running=no ... samples=6 last=stop seq=6`.
- `bootstatus` showed the same longsoak summary.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- v147 still uses a short bounded run for validation; 24h/overnight soak remains a later operator workflow.
- The summary is intentionally derived from the device JSONL file, not only from PID state, so stopped recorder sessions remain inspectable.
