# Native Init v150 Host Disconnect Classifier Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.50 (v150)` / `0.9.50 v150 HOST DISCONNECT CLASSIFIER`
Baseline: `A90 Linux init 0.9.49 (v149)`

## Summary

- Added `native_disconnect_classify.py` to separate serial bridge/cmdv1, longsoak, netservice, and NCM ping evidence.
- The classifier writes Markdown and JSON reports for long-soak disconnect triage.
- Real device classified as `serial-ok-ncm-down-or-inactive` because USB ACM/cmdv1 is healthy and optional NCM ping was not active/reachable during this run.
- v149 device-side longsoak supervisor behavior remains unchanged.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v150` | `4123f3c8caaddded397e5d7bf2c281d8ca9c26a63b3c8362edaa0f8c5286df52` |
| `stage3/linux_init/helpers/a90_longsoak` | `1d15080f6361ca194d115d05f3cefa546d97dfe963c1b0afa36f9447208f64c3` |
| `stage3/ramdisk_v150.cpio` | `4044f951d1ad4ab153aac1b1439865da45e98898db03934b1295ee79f13646a3` |
| `stage3/boot_linux_v150.img` | `117fb3f3cfaf9756e11be6c735a8069f98643486f0ed79c4baf06e7f886c16ec` |

## Validation

- Static ARM64 build for `init_v150` — PASS.
- Boot image marker checks for `A90 Linux init 0.9.50 (v150)`, `A90v150`, and `0.9.50 v150 HOST DISCONNECT CLASSIFIER` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` — PASS.
- `native_disconnect_classify.py` — classification `serial-ok-ncm-down-or-inactive`, version match true.
- Classifier probes: version/status/longsoak/netservice all `rc=0 status=ok`; NCM ping failed because optional NCM path was inactive or not configured on host during this run.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=15 failures=0` after sequential rerun.
- `native_long_soak_report.py` — `PASS host_events=15 device_samples=6`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=17/WARN=1/FAIL=0.

## Notes

- A first longsoak run was invalid because it was started concurrently with other serial-bridge clients. Sequential rerun passed; this confirms the bridge remains a single-client control path.
- v151 should bundle classifier output together with host/device JSONL, timeline, status, and log excerpts.
