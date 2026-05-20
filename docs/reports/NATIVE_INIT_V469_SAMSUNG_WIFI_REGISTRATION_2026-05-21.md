# Native Init V469 Samsung ISehWifi Registration Proof

## Status

- Decision: `v469-samsung-wifi-registration-timeout`
- Result: bounded classification passed, but native Wi-Fi connect/ping is still **not achieved**
- Evidence: `tmp/wifi/v469-samsung-wifi-registration-live-20260521-012850/manifest.json`
- Helper deployed: `a90_android_execns_probe v35`
- Helper SHA-256: `867a38a1cf55baeb30d7d15150d02e2fbcff3e491b64c3fb11bc8ba26b9430a1`

## What Changed

- V467/V468 waited for the AOSP `android.hardware.wifi@1.0::IWifi/default` target.
- V469 switches the bounded registration proof to the Samsung Android baseline targets:
  - `vendor.samsung.hardware.wifi@2.0::ISehWifi/default`
  - `vendor.samsung.hardware.wifi@2.1::ISehWifi/default`
  - `vendor.samsung.hardware.wifi@2.2::ISehWifi/default`
- The helper starts only the private service-manager, hwservicemanager, Samsung Wi-Fi HAL, and CNSS surface before running `lshal wait`.

## Guardrails

- No Wi-Fi HAL method call was made.
- No SSID/password, scan, connect, link-up, DHCP, route change, or external ping was attempted.
- `wificond`, supplicant, and hostapd were not started.
- No Android partition write, firmware mutation, rfkill write, driver bind/unbind, or boot autostart was performed.

## Live Result

| Field | Value |
| --- | --- |
| helper result | `service-query-runtime-gap` |
| helper reason | `lshal-wait-query-failed` |
| lshal result | `service-query-timeout` |
| lshal reason | `lshal-wait-timeout` |
| lshal target count | `3` |
| per-target timeout | `12000ms` |
| matched fqinstance | empty |
| service-manager started | yes |
| hwservicemanager started | yes |
| Samsung Wi-Fi HAL started | yes |
| CNSS started | yes |
| postflight clean | yes |

## Surface Result

| Phase | wlan | phy | /proc/net/wireless | Wi-Fi rfkill |
| --- | ---: | ---: | ---: | ---: |
| before | 0 | 0 | 0 | 0 |
| during | 0 | 0 | 0 | 0 |
| after cleanup | 0 | 0 | 0 | 0 |

## Interpretation

V469 rules out “we were only waiting for the wrong AOSP target” as the current blocker. Android boot-complete proves these Samsung `ISehWifi/default` targets exist, but the native private runtime still does not let the Samsung HAL register them.

The strongest blocker is now a runtime prerequisite before scan/connect:

1. Samsung Wi-Fi HAL and CNSS can be started in a bounded private namespace.
2. `lshal wait` still times out for all Samsung Wi-Fi fqinstances.
3. No WLAN/wiphy/rfkill surface appears during the bounded run.
4. The live stderr still shows the old-property-service warning and property/context symptoms later isolated by V470.

## Next Step

Do not attempt credentials, scan, connect, DHCP, or external ping yet. Fix the private property runtime first, then rerun the Samsung registration proof.
