# Native Init V567 Hwbinder Handle-Retain Plan

Date: `2026-05-21`

## Goal

V566 proved the raw hwbinder `IServiceManager.get(IWifi/default)` blocker was
not a missing service:

- String16 strict-mode tokens returned `BAD_TYPE`;
- legacy C-string token with `android.hidl.manager@1.0::IServiceManager`
  returned a non-null handle;
- `IWifi.start()` then failed because the helper freed the reply buffer before
  retaining the returned binder handle, producing an invalid-handle kernel
  transaction.

V567 repairs only that handle lifetime:

1. keep the V566 bounded dual-HAL + `wificond` + `lshal wait` sequence;
2. retain the returned hwbinder service handle before `BC_FREE_BUFFER`;
3. call `IWifi.start()` only after the retain succeeds;
4. snapshot WLAN surfaces and clean up all helper-owned children.

## Non-Goals

- no supplicant or hostapd start;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Implementation

Files:

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `scripts/revalidation/wifi_execns_helper_v92_deploy_preflight.py`
- `scripts/revalidation/native_wifi_companion_dual_hal_wificond_hwbinder_handle_retain_v567.py`

Helper artifact:

- local: `tmp/wifi/v567-a90_android_execns_probe-v92/a90_android_execns_probe`
- SHA256:
  `e7bf6dade5f5f34c0a7489c7490bf11e0534fb1a4afff66134958f1091b89880`
- marker: `a90_android_execns_probe v92`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

## Success Criteria

One of these bounded outcomes is acceptable:

1. `IWifi.start()` transaction completes and cleanup is safe;
2. `IWifi.start()` still fails, but evidence proves the service handle was
   retained before reply-buffer free and cleanup is safe;
3. service handle retain fails, proving the raw reply object parsing still
   needs repair.

Wi-Fi objective remains incomplete until native init successfully connects to
Wi-Fi and external ping passes.
