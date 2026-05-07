# Native Init v149 Long Soak Supervisor Plan

Date: `2026-05-08`
Target: `A90 Linux init 0.9.49 (v149)` / `0.9.49 v149 LONG SOAK SUPERVISOR`
Baseline: `A90 Linux init 0.9.48 (v148)`

## Summary

v149 turns the long-soak recorder from a simple start/stop helper into a
supervised device-side monitor. The target is not automatic restart yet; the
first safe step is to make recorder health visible from `status`, `bootstatus`,
`longsoak status`, and boot/manual selftest.

## Key Changes

- Extend `struct a90_longsoak_status` with `health`, `stale`, and
  `expected_max_age_ms`.
- Classify a running recorder as:
  - `warming` before the first sample appears;
  - `ok` while the newest sample is within the expected interval window;
  - `stale` when the recorder PID exists but samples stop advancing;
  - `stopped` when no recorder service is active.
- Add `a90_longsoak_health_summary()` for compact operator and selftest output.
- Add a warn-only `longsoak` selftest entry. A stale recorder is a warning, not a
  boot blocker.
- Preserve v148 host/device JSONL export and correlation behavior.

## Validation

- Static ARM64 build with `-Wall -Wextra`.
- Boot image marker checks for `A90 Linux init 0.9.49 (v149)`, `A90v149`, and
  `0.9.49 v149 LONG SOAK SUPERVISOR`.
- Real-device flash with `native_init_flash.py --verify-protocol auto`.
- Device commands: `version`, `status`, `bootstatus`, `selftest verbose`,
  `longsoak status`, `longsoak status verbose`.
- Short long-soak run with `native_long_soak.py --duration-sec 10
  --device-interval 2 --start-device`.
- Regression: integrated validation, quick soak, and local security rescan.

## Acceptance

- Known-good device reports no selftest failure.
- `longsoak status` includes `health=` and `stale=`.
- `status` and `bootstatus` include the compact health summary.
- Stale detection is visible but does not block shell/HUD entry.
