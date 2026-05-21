# Native Init V561 Companion Dual-HAL Wificond IWifi.start Plan

Date: `2026-05-21`

## Goal

Use the V560 registered dual-HAL window to attempt exactly one bounded
`IWifi.start()` transaction, but only after obtaining `IWifi/default` through
raw hwbinder.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start the bounded dual-HAL companion/wificond window;
- perform raw hwbinder `IServiceManager.get(IWifi/default)`;
- call `IWifi.start()` only if a non-null handle is returned;
- capture firmware/netdev/readiness markers and cleanup evidence.

Forbidden:

- supplicant or hostapd start;
- scan/connect/link-up;
- credential handling;
- DHCP, route changes, or external ping;
- boot partition write, reboot, or Android partition mutation.

## Success Criteria

Pass if one of these states is proven:

1. `IWifi.start()` executes and creates WLAN/firmware surface evidence; or
2. raw hwbinder cannot obtain `IWifi/default` while cleanup remains safe,
   proving the blocker is the raw client/contract path rather than registration.

Block if cleanup is not proven or if scan/connect/link-up appears.
