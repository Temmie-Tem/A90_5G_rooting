# Native Init v152 Power/Thermal Trend Plan

Date: `2026-05-08`
Target: `A90 Linux init 0.9.52 (v152)` / `0.9.52 v152 POWER THERMAL TREND`
Baseline: `A90 Linux init 0.9.51 (v151)`

## Summary

v152 adds trend extraction over the device long-soak JSONL samples. The recorder
already captures battery, power, CPU/GPU thermal, memory, load, and uptime
values; v152 makes the host report summarize first/last/min/max/delta/average so
longer overnight or workday soaks can be reviewed without manually scanning raw
JSONL.

## Key Changes

- Extend `native_long_soak_report.py` with `trends` in JSON output.
- Add Markdown trend table for `uptime_sec`, `battery_pct`, `battery_temp_c`,
  `power_w`, `cpu_temp_c`, `gpu_temp_c`, `mem_used_mb`, `mem_total_mb`, and
  `load1`.
- Keep device recorder JSONL format backward-compatible.
- Update longsoak, disconnect, and bundle host tool defaults to v152 paths.
- Device-side runtime behavior is unchanged except version/changelog bump.

## Validation

- Static ARM64 build with v152 marker strings.
- `git diff --check` and host Python `py_compile`.
- Real-device flash with `native_init_flash.py`.
- Run short longsoak, report, disconnect classifier, and bundle.
- Report JSON must include `trends` with at least `cpu_temp_c`, `gpu_temp_c`,
  `battery_pct`, `power_w`, `mem_used_mb`, and `load1` entries.
- Regression: integrated validation, quick soak, and local security rescan.

## Acceptance

- `native_long_soak_report.py` returns PASS and records trend metrics.
- Bundle includes the trend-enriched correlation JSON/Markdown.
- v152 latest verified docs point to v152 artifacts after real-device validation.
