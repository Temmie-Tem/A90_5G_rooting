# Native Init V1067 PM Observer Binder Materialization Plan

## Goal

Repair the V1066 PM observer runtime gap where service-manager actors aborted
because the private Android namespace did not materialize binder devices for the
new observer mode.

## Context

V1066 `v184` reached a final observer result, but stderr showed:

- `servicemanager`: `Binder driver '/dev/binder' could not be opened`
- `hwservicemanager`: `Binder driver could not be opened`
- `vndservicemanager`: `Binder driver '/dev/binder' could not be opened`

That means the observer was testing PM actors without the Binder substrate that
Android-positive PM startup uses.  The next step must fix this namespace defect
before drawing conclusions about `pm-service` itself.

## Scope

1. Add `wifi-companion-pm-service-trigger-observer` to the private Binder device
   materialization condition when `--allow-pm-service-trigger-observer` is set.
2. Emit observer node-status markers for `/dev/binder`, `/dev/hwbinder`, and
   `/dev/vndbinder`.
3. Build/deploy helper `v185` over NCM/TCP.
4. Rerun the bounded PM observer with the same hard guardrails.

## Guardrails

- No `mdm_helper`, CNSS actor, Wi-Fi HAL, scan/connect, credential use,
  DHCP/route, external ping, eSoC ioctl/open, or subsystem trigger.
- No boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs
  write, or Wi-Fi link-up.
- Cleanup must leave no PM/service-manager helper processes running.

## Success Criteria

- PASS if private binder nodes exist in the observer namespace and the live gate
  remains cleanup-safe with Wi-Fi/eSoC guardrails intact.
- If PM still does not open `/dev/subsys_modem`, the result must classify the
  next blocker more narrowly than V1066.
