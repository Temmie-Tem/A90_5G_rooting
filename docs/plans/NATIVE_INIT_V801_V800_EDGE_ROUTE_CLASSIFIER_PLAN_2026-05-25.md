# Native Init V801 V800 Edge Route Classifier Plan

## Goal

Classify the V800 ICNSS edge result without running another device action, and
select the smallest next gate toward native Wi-Fi readiness.

## Scope

- Read only existing manifests:
  - V800 provider-first ICNSS edge v124 replay.
  - V752 CNSS then `boot_wlan` ordering proof.
  - V720 same-window observer/reconciliation.
- Decide whether the missing QCA6390 driver link is the primary blocker or a
  side signal on this A90 ICNSS path.
- Decide whether the next live gate should combine the V800 provider-first
  service context with the V752 `boot_wlan` trigger.

## Hard Gates

- No device command.
- No Wi-Fi HAL, scan/connect, credential use, DHCP/routes, or external ping.
- No reboot, flash, boot image write, partition write, raw `esoc0`, bind/unbind,
  module load/unload, or WLAN state write.
- No Wi-Fi secret material in tracked output.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py
python3 scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py \
  --out-dir tmp/wifi/v801-v800-edge-route-plan-check \
  plan
python3 scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py run
git diff --check
```

## Expected Routing

If V800 proves service `180/74`, PeripheralManager, provider-first CNSS retry,
and ICNSS edge capture, while V752 proves `boot_wlan` reaches `wlan: Loading
driver` but not `wlan: driver loaded`, route V802 to a bounded provider-first
plus `boot_wlan` observe gate. Keep Wi-Fi HAL, scan/connect, credentials, DHCP,
routes, and external ping blocked.
