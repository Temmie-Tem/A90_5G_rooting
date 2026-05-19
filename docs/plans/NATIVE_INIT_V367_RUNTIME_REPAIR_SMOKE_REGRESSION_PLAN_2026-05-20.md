# v367 Plan: Runtime Repair Smoke Gate Regression

- date: `2026-05-20`
- scope: host-only regression for V366 approval and preexisting-node gates
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- prerequisite: V366 guarded runtime repair smoke runner

## Summary

V366 added a guard that detects pre-existing temporary target nodes before an
approved smoke run. Review found the first version computed that guard after the
approved mutation block, so it was not a reliable pre-mutation blocker.

V367 fixes that execution order and adds a host-only synthetic regression. The
regression imports `wifi_runtime_repair_smoke.py`, replaces live bridge command
functions with fixtures, and verifies the state machine without opening the
bridge or touching the device.

## Implementation

- Patch `scripts/revalidation/wifi_runtime_repair_smoke.py` so approved `run`
  evaluates preflight blockers before `create_nodes`, `property_lookup`,
  `cleanup_nodes`, or `postflight` are called.
- Add `scripts/revalidation/wifi_runtime_repair_smoke_regression.py`.
- Keep the V366 live smoke approval phrase unchanged.

## Regression Cases

The host-only regression covers:

1. no-approval clean run refuses with no mutation calls;
2. wrong phrase + full flags refuses with no mutation calls;
3. exact phrase + full flags + clean preflight reaches synthetic mutation path;
4. exact phrase + full flags + pre-existing `/dev/block/sda29` blocks before
   synthetic mutation calls;
5. exact phrase + full flags + pre-existing `/dev/binder` blocks before
   synthetic mutation calls.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_runtime_repair_smoke.py \
  scripts/revalidation/wifi_runtime_repair_smoke_regression.py

python3 scripts/revalidation/wifi_runtime_repair_smoke_regression.py \
  --out-dir tmp/wifi/v367-runtime-repair-smoke-regression-20260520-010304 \
  run

python3 scripts/revalidation/wifi_runtime_repair_smoke.py \
  --out-dir tmp/wifi/v367-v366-refusal-refresh-20260520-010326 \
  run

git diff --check
```

Expected decisions:

- regression: `runtime-repair-smoke-regression-pass`
- live no-approval refresh: `runtime-repair-smoke-approval-required`

## Acceptance

- Approved smoke with pre-existing target nodes blocks before mutation calls.
- Approved clean synthetic smoke still reaches create/stat/property/cleanup path.
- No-approval live path remains a PASS refusal with no mutation.
- No service-manager/HAL/scan/connect execution occurs.
