# Native Init V468 Extended IWifi/default Registration-Latency Proof

## Status

- Decision: `v468-iwifi-registration-longwait-wait-timeout`
- Result: bounded classification passed, but native Wi-Fi connect/ping is still **not achieved**
- Evidence: `tmp/wifi/v468-iwifi-registration-live-20260521-011411/manifest.json`
- Helper deployed: `a90_android_execns_probe v34`
- Helper SHA-256: `f43308d768d5921a645d3de7e31562609a772f5c800cbd619170c592d18dba66`

## What Changed

- V467 used a fixed 2000ms `lshal wait` window for `android.hardware.wifi@1.0::IWifi/default`.
- V468 changes the helper so the IWifi-specific `lshal wait` window follows `--timeout-sec`.
- The live V468 run used `per_target_timeout_ms=12000`.
- Scope stayed bounded to private service-manager, hwservicemanager, legacy Wi-Fi HAL, CNSS, and `lshal wait`.

## Guardrails

- `IWifi.start()` was not called.
- Wi-Fi credentials were not read.
- Scan/connect/link-up/DHCP/route/external ping were not executed.
- `wificond`, supplicant, and hostapd were not started.
- No Android partition write, firmware mutation, rfkill write, driver bind/unbind, or boot autostart was approved.

## Live Result

| Field | Value |
| --- | --- |
| helper result | `service-query-runtime-gap` |
| helper reason | `lshal-wait-query-failed` |
| lshal result | `service-query-timeout` |
| lshal reason | `lshal-wait-timeout` |
| lshal target | `android.hardware.wifi@1.0::IWifi/default` |
| lshal timeout | `12000ms` |
| matched fqinstance | empty |
| service-manager started | yes |
| hwservicemanager started | yes |
| Wi-Fi HAL started | yes |
| CNSS started | yes |
| IWifi.start executed | no |
| Wi-Fi bring-up executed | no |
| postflight clean | yes |

## Surface Result

| Phase | wlan | phy | /proc/net/wireless | Wi-Fi rfkill |
| --- | ---: | ---: | ---: | ---: |
| before | 0 | 0 | 0 | 0 |
| during | 0 | 0 | 0 | 0 |
| after cleanup | 0 | 0 | 0 | 0 |

## Stderr Signals

The live transcript included:

- duplicate hwservice specifications for Qualcomm/IMS surfaces
- SELinux service context loading from platform and vendor context files
- old property service protocol warning because `ro.property_service.version` is not set
- repeated `/dev/kmsg` write permission failures
- one `sh: no closing quote`

These are now stronger candidates than raw hwbinder parcel layout. The HAL process remained observable and cleanup-safe, but it did not register `IWifi/default` within 12 seconds and did not create a WLAN/wiphy/rfkill surface.

## Interpretation

V468 rules out “V467 only timed out because 2 seconds was too short” for the current native-init runtime. The blocker is now before Wi-Fi scan/connect:

1. The private runtime still lacks a prerequisite required for the legacy Wi-Fi HAL to register `IWifi/default`.
2. The suspicious shell/init parsing error may indicate an imported vendor init script or service script fragment is malformed under the current native namespace.
3. The property service shim may still be too weak for HAL registration, as indicated by the old property protocol warning.

## Next Step

Do not attempt credentials, scan, connect, DHCP, or external ping yet. The next useful gate is a HAL stderr/property/init-script triage:

- Capture the exact command or script path behind `sh: no closing quote`.
- Compare Android-boot HAL registration properties and native private-property contents.
- Check whether `init.svc.*`, `ro.property_service.version`, Wi-Fi HAL service properties, and vendor init fragments need a read-only materialized shim.
- Re-run the registration proof only after the registration prerequisite is identified.
