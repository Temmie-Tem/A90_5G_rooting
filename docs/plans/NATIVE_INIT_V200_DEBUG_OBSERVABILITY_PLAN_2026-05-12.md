# v200 Plan: Tracefs / Pstore Debug Observability

## Summary

v200 converts existing tracefs and pstore feasibility evidence into a safe debug
observability plan. It is intentionally read-only: the tool classifies opt-in
debug paths without mounting filesystems, enabling tracing, deleting pstore
entries, or rebooting.

## Scope

- Add `scripts/revalidation/debug_observability_plan.py`.
- Decode tracefs/ftrace/debugfs/usbmon and pstore/ramoops `CONFIG_*` values.
- Capture `tracefs full` and `pstore full`.
- Produce an opt-in matrix for:
  - tracefs mount probe
  - ftrace `current_tracer` / `tracing_on`
  - pstore mount/read
  - pstore reboot persistence test
  - debugfs broad mount
  - usbmon

## Non-Goals

- Do not mount tracefs, debugfs, or pstore.
- Do not enable tracing.
- Do not write `current_tracer` or `tracing_on`.
- Do not delete pstore entries.
- Do not trigger crash, reboot, watchdog, or fault injection tests.

## Validation

```bash
python3 -m py_compile scripts/revalidation/debug_observability_plan.py

python3 scripts/revalidation/debug_observability_plan.py \
  --out tmp/debug-observability/v200-debug-observability.md \
  --json-out tmp/debug-observability/v200-debug-observability.json
```

## Acceptance

- Current tracefs and pstore state is captured.
- The report classifies safe/blocked/maintenance-window debug paths.
- Output is private/no-follow and read-only.
- No device state is changed beyond existing read-only shell commands.
