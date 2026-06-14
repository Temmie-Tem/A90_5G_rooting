# v200 Tracefs / Pstore Debug Observability

## Summary

v200 adds a host-side debug observability planner for tracefs and pstore. This
is a plan/report generator only; latest verified native init remains
`A90 Linux init 0.9.59 (v159)`.

## Changes

- Added `scripts/revalidation/debug_observability_plan.py`.
- Reused v197 config decoding helpers from `scripts/revalidation/a90_kernel_tools.py`.
- Produced a read-only opt-in matrix for tracefs, ftrace, pstore, debugfs, and
  usbmon.

## Validation

```bash
python3 -m py_compile scripts/revalidation/debug_observability_plan.py
```

Result: PASS.

```bash
python3 scripts/revalidation/debug_observability_plan.py \
  --out tmp/debug-observability/v200-debug-observability.md \
  --json-out tmp/debug-observability/v200-debug-observability.json
```

Result: PASS.

Evidence:

- `tmp/debug-observability/v200-debug-observability.md`
- `tmp/debug-observability/v200-debug-observability.json`

Summary:

- tracefs support: yes
- tracefs mounted: no
- pstore support: yes
- pstore mounted: no
- debugfs support: yes
- usbmon support: no

Classifications:

- `tracefs mount probe`: opt-in-safe-candidate
- `ftrace current_tracer/tracing_on`: blocked-by-default
- `pstore mount/read entries`: opt-in-safe-candidate
- `pstore reboot persistence test`: maintenance-window-only
- `debugfs broad mount`: blocked-by-default
- `usbmon`: kernel-missing

## Acceptance

- Tracefs and pstore observability paths are classified without changing mount,
  tracing, pstore, reboot, watchdog, or fault-injection state.
- Future USB/serial/NCM diagnosis can start from this opt-in matrix instead of
  ad-hoc debugfs/tracefs experiments.

## Next

v201 can refresh Wi-Fi baseline evidence, but it should keep active Wi-Fi
bring-up blocked until kernel-facing WLAN/rfkill/module gates change.
