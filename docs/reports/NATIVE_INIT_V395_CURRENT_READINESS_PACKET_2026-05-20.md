# Native Init v395 Current V392 Readiness Packet

## Summary

V395 adds a host-only readiness packet for the V392 helper v21 deploy and service-manager backchain capture cycle. It consolidates current safe evidence and confirms the expected pre-approval state before any helper write or daemon start.

This update does not deploy helper v21, does not start service-manager daemons, and does not attempt Wi-Fi HAL/start/scan/connect.

## Added Tooling

- tool: `scripts/revalidation/wifi_v392_current_readiness_packet.py`
- plan: `docs/plans/NATIVE_INIT_V395_CURRENT_READINESS_PACKET_PLAN_2026-05-20.md`

The packet checks:

- V392 deploy preflight is blocked only by expected remote helper v21 mismatch plus approval gate.
- V392 live preflight is blocked only by helper v21 not yet being deployed plus approval gate.
- V392 executor remains fail-closed without approval.
- V394 post-live router points to awaiting approval.
- Optional read-only `version`, `status`, and `selftest` captures are clean.

## Evidence Refresh

Current safe refresh:

- base: `tmp/wifi/v395-refresh-20260520-072026/`
- deploy preflight: `tmp/wifi/v395-refresh-20260520-072026/deploy-preflight/`
- live preflight: `tmp/wifi/v395-refresh-20260520-072026/live-preflight/`
- no-approval executor: `tmp/wifi/v395-refresh-20260520-072026/noapproval-full/`
- post-live router: `tmp/wifi/v395-refresh-20260520-072026/post-live-router/`
- read-only health: `tmp/wifi/v395-refresh-20260520-072026/readonly/`

Key results:

- deploy preflight: `execns-helper-v21-deploy-blocked`, expected `remote-helper-v21` before approved deploy.
- live preflight: `service-manager-start-only-live-blocked`, expected `helper-v21` before approved deploy.
- no-approval executor: `v392-deploy-live-executor-approval-required`.
- post-live router: `v392-post-live-router-awaiting-approval`.
- read-only `version`, `status`, `selftest`: PASS.

## Validation

Static validation:

```text
python3 -m py_compile scripts/revalidation/wifi_v392_current_readiness_packet.py
```

Result: PASS.

Regression:

```text
python3 scripts/revalidation/wifi_v392_current_readiness_packet.py \
  --out-dir tmp/wifi/v395-readiness-regression \
  regression
```

Result:

```text
decision: v392-current-readiness-regression-pass
pass: True
device_commands_executed: False
device_mutations: False
daemon_start_executed: False
wifi_bringup_executed: False
```

Final evidence:

- `tmp/wifi/v395-final-readiness-regression/`

Current readiness packet:

```text
python3 scripts/revalidation/wifi_v392_current_readiness_packet.py \
  --out-dir tmp/wifi/v395-current-readiness-packet \
  --deploy-preflight tmp/wifi/v395-refresh-20260520-072026/deploy-preflight/manifest.json \
  --live-preflight tmp/wifi/v395-refresh-20260520-072026/live-preflight/manifest.json \
  --executor-manifest tmp/wifi/v395-refresh-20260520-072026/noapproval-full/manifest.json \
  --router-manifest tmp/wifi/v395-refresh-20260520-072026/post-live-router/manifest.json \
  --version-json tmp/wifi/v395-refresh-20260520-072026/readonly/version.json \
  --status-json tmp/wifi/v395-refresh-20260520-072026/readonly/status.json \
  --selftest-json tmp/wifi/v395-refresh-20260520-072026/readonly/selftest.json \
  packet
```

Result:

```text
decision: v392-current-readiness-ready-for-approval
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

- `tmp/wifi/v395-final-current-readiness-packet/`

V392 no-approval executor final check:

- evidence: `tmp/wifi/v395-final-v392-noapproval/`
- decision: `v392-deploy-live-executor-approval-required`
- pass: `True`
- `device_commands_executed`: `False`
- `device_mutations`: `False`
- `daemon_start_executed`: `False`
- `wifi_bringup_executed`: `False`

Post-live router final check:

- evidence: `tmp/wifi/v395-final-post-router/`
- decision: `v392-post-live-router-awaiting-approval`
- pass: `True`
- `device_commands_executed`: `False`
- `device_mutations`: `False`
- `daemon_start_executed`: `False`
- `wifi_bringup_executed`: `False`

## Current State

V392 is ready for exact-approved execution, but still blocked without approval.

Required phrases:

```text
approve v392 deploy execns helper v21 only; no daemon start and no Wi-Fi bring-up
```

```text
approve v392 service-manager backchain capture only; no Wi-Fi HAL start and no Wi-Fi bring-up
```

Approved executor command:

```bash
python3 scripts/revalidation/wifi_v392_deploy_live_executor.py \
  --out-dir tmp/wifi/v392-approved-full-$(date +%Y%m%d-%H%M%S) \
  --deploy-approval-phrase "approve v392 deploy execns helper v21 only; no daemon start and no Wi-Fi bring-up" \
  --live-approval-phrase "approve v392 service-manager backchain capture only; no Wi-Fi HAL start and no Wi-Fi bring-up" \
  --apply \
  --assume-yes \
  full
```

After the approved run, route the result:

```bash
python3 scripts/revalidation/wifi_v392_post_live_router.py \
  --out-dir tmp/wifi/v394-post-v392-route-$(date +%Y%m%d-%H%M%S) \
  --executor-manifest tmp/wifi/<v392-approved-full-run>/manifest.json \
  route
```
