# Native Init V563 Hwbinder Interface-Token Repair Plan

Date: `2026-05-21`

## Goal

V562 proved that the full dual-HAL window can register
`android.hardware.wifi@1.0::IWifi/default` through `lshal`, while the raw helper
still receives `BR_FAILED_REPLY`/service-null from `IServiceManager.get`.

V563 repairs only the raw hwbinder request framing:

1. replace the helper's C-string interface token with String16
   `Parcel::writeInterfaceToken` framing;
2. keep the existing bounded dual-HAL + `wificond` + `lshal wait` precheck;
3. call raw `IServiceManager.get(IWifi/default)`;
4. call `IWifi.start()` once only if a non-null service handle is returned;
5. snapshot WLAN surfaces and clean up all helper-owned children.

## Non-Goals

- no supplicant or hostapd start;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Contract Basis

- AOSP `Parcel::writeInterfaceToken` writes a strict-mode integer followed by a
  String16 interface token.
- AOSP `IServiceManager.hal` defines `get(string fqName, string name)` returning
  a nullable service interface.
- AOSP HIDL `hidl_string` embeds a pointer/size/owns-buffer parent and transfers
  the string body through `writeEmbeddedBuffer`.
- AOSP `IWifi.hal` defines `start()` as the bounded setup call before chip or
  scan work.

References:

- <https://android.googlesource.com/platform/system/libhwbinder/+/7919fa0d4240e22e1e0c88b99cb6b6b921646d7e/Parcel.cpp>
- <https://android.googlesource.com/platform/system/libhidl/+/refs/heads/android12L-tests-dev/transport/manager/1.0/IServiceManager.hal>
- <https://android.googlesource.com/platform/system/libhidl/+/android-8.1.0_r3/transport/HidlBinderSupport.cpp>
- <https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/IWifi.hal>

## Implementation

Files:

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `scripts/revalidation/wifi_execns_helper_v88_deploy_preflight.py`
- `scripts/revalidation/native_wifi_companion_dual_hal_wificond_hwbinder_token_repair_v563.py`

Helper artifact:

- local: `tmp/wifi/v563-a90_android_execns_probe-v88/a90_android_execns_probe`
- SHA256:
  `79091d23838d8fa1d98c1ba3868660be4ee25732c34b3bb429993c52772744e4`
- marker: `a90_android_execns_probe v88`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

## Success Criteria

One of these bounded outcomes is acceptable:

1. `IWifi.start()` transaction completes and cleanup is safe;
2. `IServiceManager.get` still returns null/fails, but the transcript proves the
   repaired String16 token path was used and cleanup is safe;
3. `lshal wait IWifi/default` fails in the same window, proving the raw call was
   correctly skipped.

Wi-Fi objective remains incomplete until native init successfully connects to
Wi-Fi and external ping passes.
