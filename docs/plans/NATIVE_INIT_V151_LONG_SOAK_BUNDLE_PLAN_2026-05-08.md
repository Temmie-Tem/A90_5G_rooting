# Native Init v151 Long Soak Bundle Plan

Date: `2026-05-08`
Target: `A90 Linux init 0.9.51 (v151)` / `0.9.51 v151 LONG SOAK BUNDLE`
Baseline: `A90 Linux init 0.9.50 (v150)`

## Summary

v151 turns the v146-v150 long-soak evidence pieces into one handoff bundle. The
host runner, device JSONL export, correlation report, and disconnect classifier
already exist; this version adds a wrapper that collects those files with live
`status`, `bootstatus`, `timeline`, `logpath`, `longsoak`, `netservice`, and
`selftest` transcripts.

## Key Changes

- Add `scripts/revalidation/native_long_soak_bundle.py`.
- Copy host JSONL, device JSONL, summary JSON, correlation report, and
  disconnect classifier output into one bundle directory.
- Capture live read-only device commands through `cmdv1` into per-command text
  files.
- Write `manifest.json` and bundle `README.md` with missing-file and failed-command
  counts.
- Keep device runtime behavior unchanged except version/changelog bump.

## Validation

- Static ARM64 build with v151 marker strings.
- `git diff --check` and host Python `py_compile`.
- Real-device flash with `native_init_flash.py`.
- Run short longsoak, correlation report, disconnect classifier, then bundle.
- Bundle PASS requires all expected evidence files to exist, all captured commands
  to return `rc=0 status=ok`, and `version` to match v151.
- Regression: integrated validation, quick soak, and local security rescan.

## Acceptance

- `tmp/soak/native-long-soak-v151-bundle/manifest.json` reports `pass=true`.
- Bundle includes host/device JSONL, correlation JSON/Markdown, disconnect
  JSON/Markdown, and command transcripts.
- v151 report records the bundle path and manifest summary.
