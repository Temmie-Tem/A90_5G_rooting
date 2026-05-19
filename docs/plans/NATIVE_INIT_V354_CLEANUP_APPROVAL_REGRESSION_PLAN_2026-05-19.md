# v354 Plan: V317 Cleanup Approval Regression Expansion

- date: `2026-05-19`
- scope: host-only regression coverage expansion for V351 cleanup gate
- boot image change: none planned
- device mutation: none planned
- status: implemented / pending validation

## Summary

V352 locked down V351 no-approval and partial-approval behavior for `run`, but
`cleanup` only had a no-approval case. v354 closes that symmetry gap by adding
cleanup phrase-only and cleanup flags-only cases.

No approved `cleanup` path is executed.

## Implementation

- Update `scripts/revalidation/wifi_v317_live_executor_regression.py`.
- Add cases:
  - `cleanup-phrase-only`
  - `cleanup-flags-only`
- Both cases must return `v317-live-executor-approval-required`, rc `1`, with
  `live_execution_approved=false`, `device_commands_executed=false`, and
  `device_mutations=false`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_live_executor.py \
  scripts/revalidation/wifi_v317_live_executor_regression.py
python3 scripts/revalidation/wifi_v317_live_executor_regression.py \
  --out-dir tmp/wifi/v352-v317-live-executor-regression \
  run
```

Expected:

- regression PASS,
- cleanup partial approval cases fail before refresh/device action,
- no live proof, daemon start, Wi-Fi bring-up, or device mutation occurs.

## Acceptance

- V351 `run` and `cleanup` have symmetric no-approval/partial-approval coverage.
- Exact V317 approval phrase and mutation flags remain required for both live paths.
