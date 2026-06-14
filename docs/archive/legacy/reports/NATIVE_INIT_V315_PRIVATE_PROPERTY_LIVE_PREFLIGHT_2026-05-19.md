# Native Init v315 Private Property Live Preflight Report

- date: `2026-05-19`
- scope: read-only live preflight before private property namespace materialization
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V315_PRIVATE_PROPERTY_LIVE_PREFLIGHT_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_private_property_live_preflight.py`

## Summary

v315 ran read-only live checks over the native bridge. The device is in the
expected baseline for a future private property namespace materialization proof.

## Evidence

| item | path | result |
| --- | --- | --- |
| live preflight | `tmp/wifi/v315-private-property-live-preflight/` | `private-property-live-preflight-ready` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_live_preflight.py
python3 scripts/revalidation/wifi_private_property_live_preflight.py \
  --out-dir tmp/wifi/v315-private-property-live-preflight \
  run
git diff --check
```

Result: PASS.

## Checks

- v314 plan prerequisite: PASS.
- native version `A90 Linux init 0.9.60 (v261)`: PASS.
- status baseline: SD writable, netservice disabled, selftest summary present.
- selftest: `fail=0`.
- storage: `backend=sd`, `rw=yes`.
- mountsd: expected mounted SD workspace.
- logpath: `/mnt/sdext/a90/logs/native-init.log`.

## Safety

- device mutations: `false`
- no `run`, write, mount, push, reboot, property service socket, daemon start,
  or Wi-Fi bring-up action was executed.

## Decision

- decision: `private-property-live-preflight-ready`
- reason: read-only live preflight passed; materialization still requires a
  separate approved implementation.
- next step: v316 approved minimal private namespace copy/materialization proof.
