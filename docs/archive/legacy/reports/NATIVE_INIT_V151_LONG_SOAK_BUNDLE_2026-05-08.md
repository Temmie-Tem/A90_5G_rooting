# Native Init v151 Long Soak Bundle Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.51 (v151)` / `0.9.51 v151 LONG SOAK BUNDLE`
Baseline: `A90 Linux init 0.9.50 (v150)`

## Summary

- Added `native_long_soak_bundle.py` to create a handoff-ready evidence directory.
- The bundle copies host/device longsoak JSONL, summary JSON, correlation reports, and disconnect classifier reports.
- The bundle captures live read-only device transcripts for `version`, `status`, `bootstatus`, `timeline`, `logpath`, `longsoak status verbose`, `netservice status`, and `selftest verbose`.
- Real-device bundle validation passed with no missing files and no failed command captures.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v151` | `55629e8f7e82b81fb5fb0e6a70af6805e6b6fa5a07c1f976fd594a6a796595ab` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v151.cpio` | `9057382e054936f4d77008c0089db24dca6b608e3f76b90ebfa53ed1cc6d406d` |
| `stage3/boot_linux_v151.img` | `027728e061f45f5f6da877748ec68001eca67b7d82b4937c4d0db6e25fc0ecdf` |

## Validation

- Static ARM64 build for `init_v151` — PASS.
- Boot image marker checks for `A90 Linux init 0.9.51 (v151)`, `A90v151`, and `0.9.51 v151 LONG SOAK BUNDLE` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=15 failures=0`.
- `native_long_soak_report.py` — `PASS host_events=15 device_samples=6`.
- `native_disconnect_classify.py` — classification `serial-ok-ncm-down-or-inactive`, version match true.
- `native_long_soak_bundle.py` — `PASS bundle=tmp/soak/native-long-soak-v151-bundle missing=0 failed_commands=0`.
- Bundle manifest: `pass=true`, `version_matches=true`, `missing_file_count=0`, `failed_command_count=0`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- Bundle output is intentionally under `tmp/soak/` and not committed.
- v152 should add trend analysis over the device JSONL values already captured by this bundle.
