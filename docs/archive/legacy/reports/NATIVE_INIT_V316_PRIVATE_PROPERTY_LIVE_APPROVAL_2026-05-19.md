# Native Init v316 Private Property Live Approval Report

- date: `2026-05-19`
- scope: approval packet for the next minimal private property namespace proof
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V316_PRIVATE_PROPERTY_LIVE_APPROVAL_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_private_property_live_approval_packet.py`

## Summary

v316 generated the approval packet for the first minimal private property
namespace proof. No device command was executed.

## Evidence

| item | path | result |
| --- | --- | --- |
| live approval packet | `tmp/wifi/v316-private-property-live-approval/` | `private-property-live-approval-ready` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_live_approval_packet.py
python3 scripts/revalidation/wifi_private_property_live_approval_packet.py \
  --out-dir tmp/wifi/v316-private-property-live-approval \
  run
git diff --check
```

Result: PASS.

## Approved Scope After Phrase

- Create a versioned private workdir under `/mnt/sdext/a90` only.
- Copy v312 generated property layout files into that private workdir only.
- Verify copied file SHA-256 values.
- Run at most a minimal static verification helper in a private namespace.
- Remove the private workdir or require native reboot for cleanup.

## Explicitly Not Approved

- Global `/dev/__properties__` replacement.
- Global bind mount over `/dev/__properties__`.
- Global `/dev/socket/property_service` creation.
- Property mutation or `setprop`-like writes.
- service-manager or hwservicemanager start.
- Wi-Fi HAL, `wificond`, `supplicant`, `hostapd`, CNSS, or diag daemon start.
- Wi-Fi scan/connect/link-up/credential/DHCP/routing.

## Required Approval Phrase

```text
approve v317 minimal private property namespace proof only; no daemon start and no Wi-Fi bring-up
```

## Decision

- decision: `private-property-live-approval-ready`
- reason: approval packet is ready; live proof still requires explicit operator
  approval.
- next step: v317 minimal private property namespace proof after explicit
  approval.
