# v353 Plan: Prefer V351 Executor in V317 Checklist

- date: `2026-05-19`
- scope: host-only operator-safety hardening for V317 handoff
- boot image change: none planned
- device mutation: none planned
- status: implemented / pending validation

## Summary

V350 originally printed the raw V340 live and cleanup commands as the primary
operator commands. After V351 added a guarded executor, the safer default is to
make the V351 executor the primary path and keep raw commands only as internal
contract evidence. v353 updates the V350 checklist accordingly.

No live proof, daemon start, or Wi-Fi bring-up is executed.

## Implementation

- Update `scripts/revalidation/wifi_v317_operator_checklist.py`.
- Add generated command fields:
  - `executor_plan_command`
  - `executor_run_command`
  - `executor_cleanup_command`
- Render V351 executor commands as the preferred operator commands.
- Keep raw V340 `live_command` and `cleanup_command` in the manifest and summary
  for contract inspection only.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_operator_checklist.py \
  scripts/revalidation/wifi_v317_live_executor.py \
  scripts/revalidation/wifi_v317_live_executor_regression.py
python3 scripts/revalidation/wifi_v317_operator_checklist.py \
  --out-dir tmp/wifi/v350-v317-operator-checklist \
  build
python3 scripts/revalidation/wifi_v317_live_executor.py \
  --out-dir tmp/wifi/v351-v317-live-executor \
  plan
python3 scripts/revalidation/wifi_v317_live_executor_regression.py \
  --out-dir tmp/wifi/v352-v317-live-executor-regression \
  run
```

Expected:

- V350 checklist ready on clean HEAD after commit.
- V351 plan ready on clean HEAD after commit.
- V352 regression pass on clean HEAD after commit.
- No device command or mutation is executed.

## Acceptance

- Operator-facing V317 live path points to V351 executor, not raw V340 command.
- Raw V340 commands remain available for command-contract inspection.
- Exact V317 approval phrase is still required before executor `run` or `cleanup`.
