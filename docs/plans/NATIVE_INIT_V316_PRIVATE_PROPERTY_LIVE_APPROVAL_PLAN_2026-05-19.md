# v316 Plan: Private Property Live Approval Packet

- date: `2026-05-19`
- scope: approval packet for the next minimal private property namespace proof
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v315 proved the current native device state is safe for a future private
property namespace proof: native v261 is running, SD workspace is read-write,
netservice is disabled, and selftest reports `fail=0`.

v316 does not execute that proof. It records the exact allowed scope and
approval phrase for v317.

## Key Changes

- Add `scripts/revalidation/wifi_private_property_live_approval_packet.py`.
- Consume:
  - `tmp/wifi/v314-private-property-materialization-executor/manifest.json`
  - `tmp/wifi/v315-private-property-live-preflight/manifest.json`
- Emit the v317 approval phrase and blocked-action list.
- Record `device_commands_executed: false`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_live_approval_packet.py
python3 scripts/revalidation/wifi_private_property_live_approval_packet.py \
  --out-dir tmp/wifi/v316-private-property-live-approval \
  run
git diff --check
```

Expected decision:

```text
private-property-live-approval-ready
```

## Required Approval Phrase

```text
approve v317 minimal private property namespace proof only; no daemon start and no Wi-Fi bring-up
```

## Acceptance

- v314 executor plan is ready.
- v315 live preflight is ready.
- No device command, ADB command, push, copy, mount, reboot, daemon start, or
  Wi-Fi bring-up action is executed.
- v317 must not proceed unless the exact approval phrase is provided.
