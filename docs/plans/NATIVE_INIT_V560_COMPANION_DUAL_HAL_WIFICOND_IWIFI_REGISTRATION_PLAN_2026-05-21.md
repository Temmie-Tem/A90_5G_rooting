# Native Init V560 Companion Dual-HAL Wificond IWifi Registration Plan

Date: `2026-05-21`

## Goal

V559 showed AOSP `IWifi/default` does not register when only the Samsung Wi-Fi
HAL binary is started, while V558 already proved Samsung `ISehWifi/default`
registration. V560 matches the Android boot-complete surface more closely by
starting both Wi-Fi HAL binaries in the bounded companion/wificond window.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start the bounded companion/wificond window;
- start both `android.hardware.wifi@1.0-service` and
  `vendor.samsung.hardware.wifi@2.0-service`;
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

Helper v85 adds:

```text
wifi-companion-dual-hal-wificond-lshal-wait-iwifi
```

The bounded child order is:

```text
servicemanager
hwservicemanager
vndservicemanager
qrtr-ns
rmt_storage
tftp_server
pd-mapper
android.hardware.wifi@1.0-service
vendor.samsung.hardware.wifi@2.0-service
cnss_diag
wificond
cnss-daemon
```

## Success Criteria

Pass if one of these states is proven:

1. AOSP `IWifi/default` registration is observed and cleanup is safe; or
2. AOSP `IWifi/default` still times out while cleanup is safe, proving the
   blocker is not only the missing legacy HAL process.

Block if cleanup is not proven, if `IWifi.start()`/scan/connect/link-up appears,
or if a Wi-Fi network interface appears unexpectedly.

## Next Gate

If AOSP IWifi registration is observed, move to one bounded `IWifi.start()`
transaction before any scan/connect or credential use.
