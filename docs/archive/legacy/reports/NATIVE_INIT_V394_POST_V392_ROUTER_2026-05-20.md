# Native Init v394 Post-V392 Router

## Summary

V394 adds a host-only result router for the approved V392 backchain capture cycle. It reads V392 executor/framechain manifests and routes to the next safe action without opening the bridge, mutating the device, starting service-manager, or attempting Wi-Fi bring-up.

This update does not deploy helper v21, does not start service-manager daemons, and does not attempt Wi-Fi HAL/start/scan/connect.

## Added Tooling

- tool: `scripts/revalidation/wifi_v392_post_live_router.py`
- plan: `docs/plans/NATIVE_INIT_V394_POST_V392_ROUTER_PLAN_2026-05-20.md`

The router classifies:

- awaiting V392 approval
- blocked V392 preflight/deploy
- scope violation
- service-manager clean enough for a future HAL start-only packet
- symbolized non-abort caller candidates
- abort-only framechain evidence
- missing ELF artifacts
- missing frame return-address map rows
- missing V392 backchain evidence
- manual-review states

## Validation

Static validation:

```text
python3 -m py_compile scripts/revalidation/wifi_v392_post_live_router.py
```

Result: PASS.

Synthetic regression:

```text
python3 scripts/revalidation/wifi_v392_post_live_router.py \
  --out-dir tmp/wifi/v394-router-regression \
  regression
```

Result:

```text
decision: v392-post-live-router-regression-pass
pass: True
device_commands_executed: False
device_mutations: False
daemon_start_executed: False
wifi_bringup_executed: False
```

Final evidence:

- `tmp/wifi/v394-final-router-regression/`

Current no-approval route:

```text
python3 scripts/revalidation/wifi_v392_post_live_router.py \
  --out-dir tmp/wifi/v394-router-current \
  --executor-manifest tmp/wifi/v393-final-v392-noapproval/manifest.json \
  route
```

Result:

```text
decision: v392-post-live-router-awaiting-approval
pass: True
remaining_blockers:
  - exact-v392-deploy-approval-phrase
  - exact-v392-backchain-capture-live-approval-phrase
device_commands_executed: False
device_mutations: False
daemon_start_executed: False
wifi_bringup_executed: False
```

Final evidence:

- `tmp/wifi/v394-final-router-current/`

V392 no-approval executor regression:

- evidence: `tmp/wifi/v394-final-v392-noapproval/`
- decision: `v392-deploy-live-executor-approval-required`
- pass: `True`
- `device_commands_executed`: `False`
- `device_mutations`: `False`
- `daemon_start_executed`: `False`
- `wifi_bringup_executed`: `False`

Read-only device health:

- evidence: `tmp/wifi/v394-readonly-20260520-071907/`
- `version`: PASS
- `status`: PASS
- `selftest`: PASS

## Current State

The next execution target remains V392 live, gated by exact approval:

```text
approve v392 deploy execns helper v21 only; no daemon start and no Wi-Fi bring-up
```

```text
approve v392 service-manager backchain capture only; no Wi-Fi HAL start and no Wi-Fi bring-up
```

After approved V392 live, run:

```bash
python3 scripts/revalidation/wifi_v392_post_live_router.py \
  --out-dir tmp/wifi/v394-post-v392-route-$(date +%Y%m%d-%H%M%S) \
  --executor-manifest tmp/wifi/<v392-approved-full-run>/manifest.json \
  route
```
