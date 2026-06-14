# Native Init V567 Hwbinder Handle Retain Report

Date: `2026-05-21`

## Goal

Verify whether the V566 invalid-handle failure is caused by freeing the
`IServiceManager.get(IWifi/default)` reply buffer before retaining the returned
hwbinder handle.

## Result

- Decision: `v567-handle-retain-start-transaction-pass`
- Pass: `True`
- Reason: raw hwbinder `IWifi.start()` completed at the transport layer after
  retaining the returned `IWifi/default` handle.
- Evidence:
  `tmp/wifi/v567-companion-dual-hal-wificond-hwbinder-handle-retain`
- Helper: `a90_android_execns_probe v92`
- Helper SHA-256:
  `e7bf6dade5f5f34c0a7489c7490bf11e0534fb1a4afff66134958f1091b89880`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v92 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded companion, service-manager, dual-HAL,
  CNSS, and `wificond` window.
- `IServiceManager.get()` used the C-string token path proven by V566.
- The returned `IWifi/default` handle was retained before freeing the reply
  buffer.
- The proof did not run supplicant, hostapd, scan/connect/link-up, credentials,
  DHCP, route changes, external ping, reboot, or boot partition writes.
- Post-run cleanup was safe and no Wi-Fi network device appeared.

## Live Evidence

```text
iwifi_start.service_handle_found=1
iwifi_start.service_handle=1
iwifi_start.service_token_wire=cstring
iwifi_start.service_retained=1
iwifi_start.start.reply.data_size=84
iwifi_start.start.reply.status_name=OK
iwifi_start.start_transaction_ok=1
iwifi_start.result=transaction-ok
wifi_companion_hal_order.surface_after_iwifi_start.wlan_count=0
wifi_companion_hal_order.surface_after_iwifi_start.phy_count=0
wifi_companion_hal_order.all_postflight_safe=1
```

## Interpretation

V567 removes the raw hwbinder transport blocker. The native helper can now:

1. reach `hwservicemanager`;
2. resolve `android.hardware.wifi@1.0::IWifi/default`;
3. retain the returned handle safely;
4. issue the `IWifi.start()` transaction without kernel invalid-handle errors.

The absence of a WLAN/PHY surface means this is not a bring-up success. It only
proves the transport path is usable and that the next blocker is the semantic
HAL result or its runtime dependencies.

## References

- HIDL transaction numbering generated for methods:
  `https://android.googlesource.com/platform/system/tools/hidl/+/ebb4ac14223651020e8f3354d610b5ac8d4ad01b/Interface.cpp`
- AOSP `IWifi.start()` contract:
  `https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/IWifi.hal`

## Next Gate

V568 should decode the returned `WifiStatus` from the successful transport
reply before any scan/connect or external ping attempt.
