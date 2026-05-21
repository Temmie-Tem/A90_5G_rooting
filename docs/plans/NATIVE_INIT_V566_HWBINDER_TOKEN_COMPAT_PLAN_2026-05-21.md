# Native Init V566 Hwbinder Token Compatibility Plan

Date: `2026-05-21`

## Goal

V565 proved that the raw hwbinder client now receives `BR_REPLY` after
`mmap()`, but `IServiceManager.get(IWifi/default)` returns status value
`-2147483647`. AOSP `Errors.h` maps this value to `BAD_TYPE`, which points to
parcel/type mismatch rather than a missing service: `lshal wait
android.hardware.wifi@1.0::IWifi/default` passed in the same bounded window.

V566 narrows that blocker without Wi-Fi bring-up:

1. keep the V565 bounded dual-HAL + `wificond` + `lshal wait` sequence;
2. attempt raw `IServiceManager.get(IWifi/default)` with both hwbinder token
   wire formats observed in AOSP history:
   - String16 strict-mode header;
   - legacy C-string token;
3. call `IWifi.start()` only if a non-null service handle is returned;
4. snapshot WLAN surfaces and clean up all helper-owned children.

## Non-Goals

- no supplicant or hostapd start;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Contract Basis

- AOSP HIDL generator reserves user transactions from
  `FIRST_CALL_TRANSACTION = 0x00000001`, so `IServiceManager.get` remains
  transaction `1`.
- AOSP `IServiceManager.hal` defines `get(string fqName, string name)` returning
  a nullable service interface.
- AOSP `IWifi.hal` orders `start()` after `registerEventCallback` and
  `isStarted`, so the current `IWifi.start` transaction code remains `3`.
- AOSP libhwbinder history contains both token styles: older `Parcel` writes a
  C-string token, while newer `Parcel` writes strict-mode plus String16.

References:

- <https://android.googlesource.com/platform/system/tools/hidl/+/ebb4ac14223651020e8f3354d610b5ac8d4ad01b/Interface.cpp>
- <https://android.googlesource.com/platform/system/libhidl/+/refs/heads/android12L-tests-dev/transport/manager/1.0/IServiceManager.hal>
- <https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/IWifi.hal>
- <https://android.googlesource.com/platform/system/libhwbinder/+/9be04ce75cd5b6116550ce2dd9210c49d98daff1/Parcel.cpp>
- <https://android.googlesource.com/platform/system/libhwbinder/+/7919fa0d4240e22e1e0c88b99cb6b6b921646d7e/Parcel.cpp>
- <https://android.googlesource.com/platform/system/core/+/refs/tags/platform-tools-35.0.2/libutils/binder/include/utils/Errors.h>

## Implementation

Files:

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `scripts/revalidation/wifi_execns_helper_v91_deploy_preflight.py`
- `scripts/revalidation/native_wifi_companion_dual_hal_wificond_hwbinder_token_compat_v566.py`

Helper artifact:

- local: `tmp/wifi/v566-a90_android_execns_probe-v91/a90_android_execns_probe`
- SHA256:
  `3246fade6f0a484b6cbc416a64c3884d686dc4f9b2dd35ae8a3f656516893f85`
- marker: `a90_android_execns_probe v91`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

## Success Criteria

One of these bounded outcomes is acceptable:

1. `IWifi.start()` transaction completes and cleanup is safe;
2. `IServiceManager.get` still returns null/fails, but evidence proves both
   token formats were tested and shows the returned status classification;
3. `lshal wait IWifi/default` fails in the same window, proving the raw call was
   correctly skipped.

Wi-Fi objective remains incomplete until native init successfully connects to
Wi-Fi and external ping passes.
