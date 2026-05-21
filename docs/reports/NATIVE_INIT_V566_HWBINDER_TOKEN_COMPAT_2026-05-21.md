# Native Init V566 Hwbinder Token Compatibility Report

Date: `2026-05-21`

## Goal

Determine whether the raw hwbinder `IServiceManager.get()` failure was caused
by an interface-token wire-format mismatch. The proof tries both modern
String16 strict-mode tokens and the older libhwbinder C-string token shape in
the same bounded dual-HAL plus `wificond` window.

## Result

- Decision: `v566-token-compat-start-transaction-failed`
- Pass: `True`
- Reason: raw `IServiceManager.get(IWifi/default)` reached a non-null service
  handle with the legacy C-string token, but `IWifi.start()` did not complete
  cleanly.
- Evidence: `tmp/wifi/v566-companion-dual-hal-wificond-hwbinder-token-compat`
- Helper: `a90_android_execns_probe v91`
- Helper SHA-256:
  `3246fade6f0a484b6cbc416a64c3884d686dc4f9b2dd35ae8a3f656516893f85`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v91 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded companion, service-manager, dual-HAL,
  CNSS, and `wificond` window.
- The proof did not run supplicant, hostapd, scan/connect/link-up, credentials,
  DHCP, route changes, external ping, reboot, or boot partition writes.
- Post-run child cleanup was reported safe.
- Post-run Wi-Fi network surface remained absent.

## Live Evidence

```text
iwifi_start.service_handle_found=1
iwifi_start.service_handle=1
iwifi_start.service_token_wire=cstring
iwifi_start.start_transaction_ok=0
iwifi_start.result=transaction-failed
wifi_companion_hal_order.surface_after_iwifi_start.wlan_count=0
wifi_companion_hal_order.surface_after_iwifi_start.phy_count=0
wifi_companion_hal_order.all_postflight_safe=1
```

Relevant kernel evidence:

```text
binder: ... got transaction to invalid handle
```

## Interpretation

V566 proves the previous raw `IWifi/default` lookup failure was not just timing
or registration. The working path on this device requires the legacy
libhwbinder-style C-string interface token for `IServiceManager@1.0`. The
subsequent `IWifi.start()` failure pointed to a separate handle-lifetime issue:
the returned binder handle was used after freeing the reply buffer.

The V566 wrapper parser was corrected after this run to include
`iwifi_start.*` keys. The raw evidence above is the authoritative result.

## References

- AOSP `IServiceManager.get()` contract:
  `https://android.googlesource.com/platform/system/libhidl/+/refs/heads/android12L-tests-dev/transport/manager/1.0/IServiceManager.hal`
- Older libhwbinder C-string interface token path:
  `https://android.googlesource.com/platform/system/libhwbinder/+/9be04ce75cd5b6116550ce2dd9210c49d98daff1/Parcel.cpp`
- Newer libhwbinder String16 interface token path:
  `https://android.googlesource.com/platform/system/libhwbinder/+/7919fa0d4240e22e1e0c88b99cb6b6b921646d7e/Parcel.cpp`

## Next Gate

V567 should retain the service handle before freeing the hwbinder reply buffer,
then retry the bounded `IWifi.start()` transport proof without scan/connect or
external ping.
