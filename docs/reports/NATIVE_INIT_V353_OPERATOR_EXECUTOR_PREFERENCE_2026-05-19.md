# v353 Operator Executor Preference Report

- date: `2026-05-19`
- scope: host-only operator-safety hardening for V317 handoff
- device command: none
- device mutation: none
- result: `PENDING VALIDATION`

## Summary

v353 changes the V350 operator checklist so that the preferred live and cleanup
commands go through the V351 fail-closed executor. Raw V340 live/cleanup commands
remain in the evidence for inspection, but they are no longer the primary
operator path.

## Code Change

- `scripts/revalidation/wifi_v317_operator_checklist.py`
  - adds V351 executor `plan`, `run`, and `cleanup` commands to the manifest
  - renders executor commands under preferred commands
  - moves raw V340 live/cleanup commands under internal raw commands

## Validation Plan

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

## Safety

- No live V317 proof is executed.
- No daemon start or Wi-Fi bring-up is performed.
- No device mutation is expected during validation.
