# v352 Plan: V317 Live Executor Regression

- date: `2026-05-19`
- scope: host-only regression tests for V351 executor guard
- boot image change: none planned
- device mutation: none planned
- status: implemented / pending post-commit clean-head run

## Summary

V351 added the guarded executor for the V317 minimal live proof. v352 adds a
host-only regression suite that locks down the most important executor behavior:
no approval or partial approval must fail before any device action, while the
plan path must remain host-only and reflect the current tree cleanliness.

No approved `run` or `cleanup` path is executed by this regression.

## Implementation

- Add `scripts/revalidation/wifi_v317_live_executor_regression.py`.
- Cases:
  - `run-no-approval`
  - `run-phrase-only`
  - `run-flags-only`
  - `cleanup-no-approval`
  - `plan-current-state`
- Validate for each case:
  - expected decision and rc,
  - `live_execution_approved=false`,
  - `device_commands_executed=false`,
  - `device_mutations=false`,
  - no-approval cases return before running refresh steps.
- Write evidence under `tmp/wifi/v352-v317-live-executor-regression/`.

## Validation

Pre-commit validation:

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_live_executor.py \
  scripts/revalidation/wifi_v317_live_executor_regression.py
python3 scripts/revalidation/wifi_v317_live_executor_regression.py \
  --out-dir tmp/wifi/v352-v317-live-executor-regression \
  run
```

Expected pre-commit result:

- regression PASS,
- `plan-current-state` may observe dirty-tree blocking,
- no live proof, daemon start, Wi-Fi bring-up, or device mutation occurs.

Post-commit validation:

```bash
python3 scripts/revalidation/wifi_v317_live_executor_regression.py \
  --out-dir tmp/wifi/v352-v317-live-executor-regression \
  run
```

Expected post-commit result:

```text
decision: v317-live-executor-regression-pass
pass: True
device_commands_executed: false
device_mutations: false
```

## Acceptance

- V352 reaches regression PASS both before and after commit.
- Partial approval combinations continue to fail closed.
- The regression never executes an approved V317 live path.
