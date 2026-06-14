# Native Init V801 V800 Edge Route Classifier Report

## Result

- decision: `v801-provider-first-boot-wlan-observe-selected`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py`
- evidence: `tmp/wifi/v801-v800-edge-route-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py
python3 scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py \
  --out-dir tmp/wifi/v801-v800-edge-route-plan-check \
  plan
python3 scripts/revalidation/native_wifi_v800_edge_route_classifier_v801.py run
```

V801 was host-only. It did not execute any device command.

## Evidence Summary

| Signal | V800 | V752 |
| --- | --- | --- |
| service `180/74` | positive | not the target |
| PeripheralManager exact query | yes | not the target |
| provider-first CNSS retry | started | not the target |
| ICNSS driver link | present | present in edge capture |
| QCA6390 driver link | absent | absent in edge capture |
| `boot_wlan` write | not executed | executed |
| `wlan: Loading driver` | not expected | present |
| `wlan: driver loaded` | absent | absent |
| WLFW/BDF/`wlan0` | absent | absent |
| Wi-Fi HAL/scan/connect/external ping | not executed | not executed |

## Classification

V800 and V752 answer different halves of the same blocker:

```text
V800: service74 + PeripheralManager + provider-first CNSS retry + ICNSS edge
V752: CNSS lower context + boot_wlan -> HDD loading, then driver-loaded stall
```

The unbound `cnss-qca6390` platform node is not enough to select a QCA6390 bind
or custom-kernel path. The stock native path repeatedly shows ICNSS bound while
QCA6390/WLFW/BDF/`wlan0` remain absent, and V752 proves the driver does not
advance past HDD init even after `boot_wlan`.

The next smallest live test is therefore not another provider-only replay and
not another lower-only `boot_wlan` replay. It should combine the two proven
halves:

```text
service74/provider-first CNSS context
  -> bounded boot_wlan observe
  -> classify HDD/ICNSS-QMI/WLFW progression
```

## Safety

- Host-only classifier; no device command executed.
- No Wi-Fi HAL, scan/connect, credential use, DHCP/routes, external ping,
  reboot, boot image write, partition write, raw `esoc0`, bind/unbind, module
  load/unload, or WLAN state write.
- No Wi-Fi secret material written to tracked output.

## Next

V802 should implement a bounded live proof that reuses the V800 provider-first
service context and then performs a V752-style `boot_wlan` observe. It must
still block Wi-Fi HAL, supplicant, scan/connect, credentials, DHCP/routes, and
external ping. Success is not Wi-Fi connection yet; success is identifying
whether provider-first context moves the `boot_wlan` boundary from
`wlan: Loading driver` toward ICNSS-QMI/WLFW/BDF/wiphy/`wlan0`.
