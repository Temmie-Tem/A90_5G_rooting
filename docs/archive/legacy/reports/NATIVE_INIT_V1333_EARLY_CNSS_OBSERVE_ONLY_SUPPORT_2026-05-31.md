# Native Init V1333 Early-CNSS Observe-only Support

## Summary

- Cycle: `V1333`
- Type: source/build-only helper support
- Decision: `v1333-early-cnss-observe-only-build-pass`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1333-early-cnss-observe-only-support/manifest.json`
  - `tmp/wifi/v1333-early-cnss-observe-only-support/summary.md`
- Script: `scripts/revalidation/native_wifi_early_cnss_observe_only_support_v1333.py`
- Helper: `a90_android_execns_probe v277`
- Helper SHA256: `3a61125bd3e2bad9cda8dcac2df75184c3df369ada4a9a0010681c49788a6fd9`

V1333 adds an observe-only trigger gate for the existing
`wifi-companion-mdm-helper-cnss-before-subsys-trigger-capture` helper path.
The new `--subsys-trigger-gate observe-only` value keeps `/dev/subsys_esoc0`
closed even if a WLFW precondition is observed. This matches the V1332 next
gate: observe native early-CNSS/WLFW parity before any `per_proxy`/eSoC trigger.

## Added Contract

| item | value |
| --- | --- |
| helper_version | `a90_android_execns_probe v277` |
| new_gate | `--subsys-trigger-gate observe-only` |
| observe_marker | `cnss_before_esoc.observe_only_gate` |
| trigger_marker | `cnss_before_esoc.wlfw_trigger_ready` |
| observed_result | `cnss_before_esoc.result=wlfw-precondition-observed-observe-only-no-open` |
| safety_result | `observe-only-gate-kept-subsys-esoc0-closed` |

## Validation

The build gate produced a static aarch64 helper at
`stage3/linux_init/helpers/a90_android_execns_probe_v277`. `readelf` confirmed
no `INTERP` segment and no dynamic section. Required source and binary strings
for the observe-only gate and result contract were present.

## Next

- V1334: deploy helper `v277` only.
- V1335: run the bounded native early-CNSS WLFW parity observer with
  `/dev/subsys_esoc0` kept closed.

## Safety

Source/build-only. No device command, helper deploy, actor start, tracefs write,
live eSoC open/ioctl/notify, PMIC/GPIO write, Wi-Fi HAL start, scan/connect,
credential use, DHCP/routes, external ping, flash, boot image write, or
partition write occurred.
