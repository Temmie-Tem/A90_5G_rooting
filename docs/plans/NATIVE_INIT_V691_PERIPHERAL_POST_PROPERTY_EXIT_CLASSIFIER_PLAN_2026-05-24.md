# Native Init V691 Peripheral Post-Property Exit Classifier Plan

## Objective

V691 classifies the V690 post-property provider exit without running new device
commands. V690 proved that helper v115 acknowledges the exact private
`vendor.peripheral.*.state=OFFLINE` writes and removes the previous property
set `0x18` blocker, but `pm-service` and `pm-proxy` still exit before the
observe window.

## Scope

- Use existing V690 live evidence only.
- Parse:
  - private property-service shim requests;
  - `pm-service` and `pm-proxy` child status;
  - provider FD summaries;
  - residual process list after the bounded helper run;
  - remaining property-read denials and Binder/WLFW marker counts.
- Decide whether the next gate should be more property-area materialization or
  targeted provider exit/registration capture.

## Guardrails

- no bridge/device command;
- no helper deploy;
- no daemon/service start;
- no Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, DHCP, route,
  credential, or external ping;
- no boot image or partition write.

## Success Criteria

- V690 evidence is present and has decision
  `v690-provider-post-property-start-gap-classified`;
- V690 property ack regression is false;
- no `Unable to set property ... 0x18` line remains;
- classifier identifies whether provider processes persist after the helper
  window;
- classifier records the next concrete blocker.

## Next Gate

If provider processes do not persist, V692 should add targeted provider
exit/registration observability before changing functionality again:

1. capture `pm-service`/`pm-proxy` exit path with a bounded provider-only mode;
2. snapshot vndservicemanager service registry around provider start;
3. preserve the exact private property ack but keep Wi-Fi HAL, credentials,
   scan/connect, DHCP, routing, and external ping blocked.
