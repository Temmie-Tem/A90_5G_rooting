# Native Init V562 Lshal-Then-IWifi.start Report

Date: `2026-05-21`

## Goal

Separate timing from raw hwbinder client errors by running
`lshal wait android.hardware.wifi@1.0::IWifi/default` and then attempting raw
`IServiceManager.get(IWifi/default)` in the same bounded dual-HAL
companion/wificond window.

## Result

- Decision: `v562-lshal-pass-raw-get-service-null`
- Pass: `True`
- Reason: same-window `lshal wait` passed but raw hwbinder get still returned
  service-null.
- Evidence: `tmp/wifi/v562-companion-dual-hal-wificond-lshal-then-iwifi-start`
- Helper: `a90_android_execns_probe v87`
- Helper SHA-256:
  `44fbabd9a67ea27625711bfff3ce564ca551e77acc42ad7c68f2a06836ca089c`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v87 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded dual-HAL companion/wificond window.
- `lshal wait` confirmed `android.hardware.wifi@1.0::IWifi/default`.
- Raw hwbinder did not obtain the handle, so `IWifi.start()` was not executed.
- Supplicant, hostapd, scan/connect/link-up, credentials, DHCP, route changes,
  external ping, reboot, and boot partition writes were not executed.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Result

```text
wifi_hal_micro_query.result=service-query-pass
wifi_hal_micro_query.reason=lshal-wait-exit-zero
wifi_hal_micro_query.matched_fqinstance=android.hardware.wifi@1.0::IWifi/default
wifi_companion_hal_order.service_query_result=0
iwifi_start.service_handle_found=0
iwifi_start.transaction_executed=0
iwifi_start.result=service-null
wifi_companion_hal_order.iwifi_start_result=20
wifi_companion_hal_order.result=iwifi-service-null
wifi_companion_hal_order.all_postflight_safe=1
post-run residue: none
wifi netdev: none
```

## Interpretation

V562 proves the native runtime surface is now good enough for Android's own
`lshal` to see AOSP `IWifi/default` in the same window where the raw client
fails. The current blocker is therefore not process order, HAL registration, or
simple timing. It is the raw hwbinder `IServiceManager.get` parcel/object
contract or handle extraction logic.

## Next Gate

V563 should be code-only or bounded-read proof focused on hwbinder contract
repair:

1. compare the helper's raw parcel layout with Android HIDL service-manager
   client behavior;
2. add a minimal raw `IServiceManager.list()` or `debugDump()` proof if needed;
3. only after raw `get(IWifi/default)` returns a non-null handle, retry
   bounded `IWifi.start()`;
4. keep scan/connect, credentials, DHCP, routes, and external ping blocked.
