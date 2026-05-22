# Native Init V639 Sibling Warning Attribution Plan

- date: `2026-05-23 KST`
- cycle: `v639`
- scope: host-only classifier
- target: classify the V638 `pm_qos` warning regression before any further
  sibling SSCTL live retry

## Background

V638 proved that firmware-backed ADSP/CDSP/SLPI child writes can all return,
but the run still produced new `pm_qos_add_request()` kernel warnings and did
not advance sibling `sysmon-qmi`, service `74`, WLAN-PD, WLFW/BDF,
firmware-ready, or `wlan0`.

Earlier runs provide the needed contrast:

- V619: all-sibling direct boot-node replay plus Android-order companion
  produced sibling `sysmon-qmi` but also `pm_qos` kernel warnings.
- V635: firmware-backed CDSP-only proof returned and was warning-free, but did
  not advance lower QMI/WLAN markers.
- V636: CDSP-online plus the V598-class lower path reproduced service `180`
  and stayed warning-free, but did not publish service `74`.

## Guardrails

V639 must not:

- contact the device;
- write sysfs, DSP boot nodes, `boot_wlan`, `qcwlanstate`, or
  `shutdown_wlan`;
- start daemons, service-manager, CNSS, Wi-Fi HAL, supplicant, or hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally;
- build, flash, reboot, or alter the live native baseline.

## Inputs

- V638 live evidence:
  `tmp/wifi/v638-firmware-sibling-live-20260523-060104/manifest.json`
- V638 dmesg:
  `tmp/wifi/v638-firmware-sibling-live-20260523-060104/native/dmesg-after-sibling.txt`
- V638 sibling state snapshots:
  `tmp/wifi/v638-firmware-sibling-live-20260523-060104/native/state-after-*.txt`
- V619 live evidence:
  `tmp/wifi/v619-android-order-post-sysmon-observer-run/manifest.json`
- V635 live evidence:
  `tmp/wifi/v635-cdsp-proof-20260523-052940/manifest.json`
- V636 live evidence:
  `tmp/wifi/v636-cdsp-v598-live-20260523-054728/manifest.json`

## Checks

1. Attribute V638 `pm_qos_add_request()` timestamps to the nearest preceding
   ADSP/CDSP/SLPI PIL event.
2. Compare V638 all-sibling warnings against V619 all-sibling warnings.
3. Compare both warning runs against warning-free V635 CDSP-only and V636
   CDSP+V598 evidence.
4. Confirm V638 lower Wi-Fi markers stayed absent despite all nodes returning.
5. Confirm V638 cleanup returned the device to healthy native baseline.
6. Decide whether a single-node retry is justified or whether direct sibling
   boot-node writes must remain blocked.

## Success Criteria

V639 passes if it produces one of these host-only decisions:

- `v639-all-sibling-warning-attributed-single-node-unresolved`
- `v639-cdsp-only-warning-free-contrast-classified`
- `v639-warning-evidence-gap`

Passing V639 does not authorize CNSS/HAL, scan/connect, credentials, DHCP,
routes, external ping, or another direct all-sibling write. If attribution is
insufficient, the next gate should stay host-only or use a narrower
warning-free path already proven by evidence.
