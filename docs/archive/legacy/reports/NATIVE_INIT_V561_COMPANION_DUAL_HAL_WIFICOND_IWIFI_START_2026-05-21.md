# Native Init V561 Companion Dual-HAL Wificond IWifi.start Report

Date: `2026-05-21`

## Goal

After V560 observed AOSP `IWifi/default` registration in the dual-HAL
companion/wificond window, V561 attempted the next bounded action: one raw
hwbinder `IServiceManager.get(IWifi/default)` followed by `IWifi.start()` only
if a non-null handle was returned.

## Result

- Decision: `v561-iwifi-start-service-null`
- Pass: `True`
- Reason: `IWifi/default` handle was not returned despite V560 registration
  proof.
- Evidence: `tmp/wifi/v561-companion-dual-hal-wificond-iwifi-start`
- Helper: `a90_android_execns_probe v86`
- Helper SHA-256:
  `7564fa10547f4d5208a2062785dea34ea9d30bd116f08daf4ce289266cfa6314`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v86 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded dual-HAL companion/wificond window.
- `IWifi.start()` was not executed because no service handle was returned.
- Supplicant, hostapd, scan/connect/link-up, credentials, DHCP, route changes,
  external ping, reboot, and boot partition writes were not executed.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Result

```text
iwifi_start.descriptor=android.hardware.wifi@1.0::IWifi
iwifi_start.instance=default
iwifi_start.binder_protocol=8
iwifi_start.context.acquire.handle=0
iwifi_start.context.acquire.weak_rc=0
iwifi_start.context.acquire.strong_rc=0
iwifi_start.get.failed_reply=1
iwifi_start.service_handle_found=0
iwifi_start.transaction_executed=0
iwifi_start.result=service-null
iwifi_start.reason=IWifi-default-handle-not-returned
wifi_companion_hal_order.iwifi_start_result=20
wifi_companion_hal_order.surface_after_iwifi_start.wlan_count=0
wifi_companion_hal_order.surface_after_iwifi_start.phy_count=0
wifi_companion_hal_order.all_postflight_safe=1
post-run residue: none
wifi netdev: none
```

## Interpretation

V561 does not disprove V560. It proves a narrower mismatch:

- `lshal wait` can observe AOSP `IWifi/default` registration in the dual-HAL
  window.
- The raw hwbinder `IServiceManager.get(IWifi/default)` client still receives
  failed replies and cannot obtain a handle.
- Therefore `IWifi.start()` is still blocked before execution.

The next useful step is not scan/connect. It is a same-window comparison that
first proves `lshal wait IWifi/default` succeeds, then immediately attempts the
raw hwbinder get/start path in that same process window. That separates timing
from parcel/client contract errors.

## Next Gate

Recommended V562:

1. keep the V560 dual-HAL companion/wificond window;
2. run `lshal wait android.hardware.wifi@1.0::IWifi/default`;
3. only if `lshal wait` passes, attempt the raw `IServiceManager.get` and
   bounded `IWifi.start()`;
4. still block credentials, scan/connect/link-up, DHCP, routes, and external
   ping.
