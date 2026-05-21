# Native Init V559 Companion Plus HAL Plus Wificond IWifi Registration Plan

Date: `2026-05-21`

## Goal

V558 observed Samsung `ISehWifi/default` registration in the 11-child native
private namespace. That does not automatically prove the AOSP
`android.hardware.wifi@1.0::IWifi/default` service exists. V559 checks the AOSP
IWifi registration surface before any `IWifi.start()` or scan/connect work.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start the same bounded 11-child V558 window;
- run `/system/bin/lshal wait android.hardware.wifi@1.0::IWifi/default`;
- collect stdout/stderr, dmesg, process, QRTR, and runtime-surface evidence;
- cleanup all helper-owned children.

Forbidden:

- `IWifi.start()` transaction;
- supplicant or hostapd start;
- scan/connect/link-up;
- credential handling;
- DHCP, route changes, or external ping;
- boot partition write, reboot, or Android partition mutation.

## Helper Change

Helper v84 adds:

```text
wifi-companion-hal-wificond-lshal-wait-iwifi
```

The process window still starts the Samsung HAL only. The query target switches
from Samsung `ISehWifi/default` to AOSP `IWifi/default`.

## Success Criteria

Pass if one of these states is proven:

1. AOSP `IWifi/default` registration is observed and cleanup is safe; or
2. AOSP `IWifi/default` times out while cleanup is safe, proving that Samsung
   extension registration alone is not enough to call `IWifi.start()`.

Block if cleanup is not proven, if `IWifi.start()`/scan/connect/link-up appears,
or if a Wi-Fi network interface appears unexpectedly.

## Next Gate

If AOSP IWifi registration times out, the next controlled test is a full
Android-like dual-HAL window that starts both
`android.hardware.wifi@1.0-service` and
`vendor.samsung.hardware.wifi@2.0-service` before retrying AOSP registration.
