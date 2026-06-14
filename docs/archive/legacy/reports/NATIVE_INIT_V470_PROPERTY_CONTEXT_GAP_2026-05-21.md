# Native Init V470 Property Context Gap Report

## Status

- Decision: `v470-property-context-gap-confirmed`
- Result: native Wi-Fi connect/ping is still **not achieved**
- Evidence: `tmp/wifi/v470-native-property-gap-20260521-013907/property-analysis.json`
- Helper deployed: `a90_android_execns_probe v36`

## Why This Matters

V468/V469 repeatedly showed the warning that `ro.property_service.version` was not set. V470 directly tested private `getprop` lookups through the helper namespace and confirmed that the existing V317 property root only covers the earlier minimal build-property set.

## Lookup Result

| Category | Keys | Result |
| --- | ---: | --- |
| probed keys | 19 | helper rc/status stayed `0/ok` |
| returned values | 4 | `ro.build.version.sdk`, `ro.hardware`, `ro.product.name`, `ro.vendor.build.version.sdk` |
| empty values | 15 | boot/service/Wi-Fi/property-service keys |
| stderr context warnings | 19/19 commands | each command emitted missing-context/access-denied property warnings |

## Returned Values

| Key | Value |
| --- | --- |
| `ro.build.version.sdk` | `31` |
| `ro.hardware` | `qcom` |
| `ro.product.name` | `r3qks` |
| `ro.vendor.build.version.sdk` | `30` |

## Empty Runtime Keys

| Key |
| --- |
| `ro.property_service.version` |
| `sys.boot_completed` |
| `dev.bootcomplete` |
| `wifi.interface` |
| `wlan.driver.status` |
| `init.svc.servicemanager` |
| `init.svc.hwservicemanager` |
| `init.svc.vendor.wifi_hal_ext` |
| `init.svc.vendor.wifi_hal_legacy` |
| `init.svc.vendor.wifi_hal` |
| `init.svc.wificond` |
| `init.svc.wpa_supplicant` |
| `init.svc.cnss-daemon` |
| `init.svc.cnss_diag` |

## Root Cause

The current device-side private property tree is still the V317 minimal layout:

- `property_info`
- `properties_serial`
- `u:object_r:bootloader_prop:s0`
- `u:object_r:build_prop:s0`
- `u:object_r:build_vendor_prop:s0`

That layout was enough for four read-only build properties, but it does not describe the property contexts needed by bionic, service-manager, Wi-Fi HAL, CNSS, or `lshal` in the current registration proof.

## Decision

The next useful repair is not Wi-Fi credential/scan/connect. The next repair is an expanded private property runtime with `property_info` plus per-context property areas for the runtime keys observed in V470.
