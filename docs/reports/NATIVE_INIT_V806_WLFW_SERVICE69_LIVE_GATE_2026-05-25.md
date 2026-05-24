# Native Init V806 WLFW Service69 Live Gate Report

## Result

- decision: `v806-service69-absent-after-provider-first-boot-wlan`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py`
- evidence: `tmp/wifi/v806-wlfw-service69-live-gate/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py

python3 scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py \
  --out-dir tmp/wifi/v806-wlfw-service69-live-gate-plan-check \
  plan

python3 scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py run
```

V806 reused the V802 current-boot orchestrator and direct provider-first
`boot_wlan` arm.

## Evidence Summary

| Signal | Result |
| --- | --- |
| V805 route input | pass |
| provider-first context | executed |
| service74 gate | open |
| PeripheralManager exact query | true |
| initial CNSS suppressed | true |
| CNSS retry | started |
| `boot_wlan` observe | executed |
| QRTR RX/TX markers | `1 / 1` |
| service-notifier markers | `2` |
| `wlan: Loading driver` | `1` |
| `qcwlanstate` readbacks | `35` |
| QRTR service `69` after boot observe | `0` |
| QRTR service `74/180` after boot observe | `0 / 0` |
| WLFW / ICNSS-QMI / FW-ready | `0 / 0 / 0` |
| BDF / wiphy / `wlan0` | `0 / 0 / 0` |
| forbidden connect actions | not executed |
| postflight cleanup | v724 version/selftest healthy |

## Classification

V806 proves that the best current below-HAL path still stops before WLFW service
publication:

```text
provider-first service74/180 context
  -> CNSS retry observable
  -> boot_wlan observe
  -> wlan: Loading driver
  -> qcwlanstate remains OFF
  -> QRTR service69 absent
  -> no ICNSS-QMI / FW_READY / BDF / wiphy / wlan0
```

The missing point is not another provider-first replay and not a Wi-Fi HAL or
credential issue. The next useful classifier is the pre-WLFW publication
contract: which native prerequisite still prevents the WLAN firmware service
`0x45` / `69` from being published after modem/PIL/QRTR/provider activity is
already present.

## Safety

- No custom kernel flash, boot image write, or partition write outside the
  current-boot prep path.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credential use,
  DHCP, route change, or external ping.
- No direct `qcwlanstate` write.
- No `esoc0` open/hold.
- No bind/unbind, `driver_override`, or module load/unload.
- Runner-owned reboot cleanup returned native v724 to healthy status.
- No Wi-Fi secret material was written to tracked output.

## Next

V807 should be host-only first. It should compare source and existing evidence
for the pre-WLFW publication prerequisites, especially:

- service-notifier `74/180` after `boot_wlan` versus only before it;
- whether WLAN-PD publication requires a live `service-notifier` subscription
  during ICNSS lookup rather than a transient provider-first window;
- whether firmware/RFS/tftp/pd-mapper evidence proves `wlanmdsp.mbn` is served;
- whether another bounded live gate should keep companion services alive across
  the entire `boot_wlan` observe window.
