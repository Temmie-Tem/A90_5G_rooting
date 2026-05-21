# Native Init V568 IWifi.start Status Decode Plan

Date: `2026-05-21`

## Goal

V567 proved the raw hwbinder path can obtain and retain
`android.hardware.wifi@1.0::IWifi/default`, then complete the `IWifi.start()`
transport transaction with cleanup safe. However no `wlan`/`phy` surface or
firmware readiness marker appeared.

V568 decodes the application-level HIDL `WifiStatus` returned by
`IWifi.start()` so the next blocker is not hidden behind transport success.

## Non-Goals

- no supplicant or hostapd start;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Contract Basis

AOSP `android.hardware.wifi@1.0::WifiStatus` contains:

- `WifiStatusCode code`;
- `string description`.

The success path is only valid when both hwbinder transport succeeds and
`WifiStatus.code == SUCCESS`.

Reference:

- <https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/types.hal>

## Implementation

Files:

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `scripts/revalidation/wifi_execns_helper_v93_deploy_preflight.py`
- `scripts/revalidation/native_wifi_companion_dual_hal_wificond_iwifi_start_status_v568.py`

Helper artifact:

- local: `tmp/wifi/v568-a90_android_execns_probe-v93/a90_android_execns_probe`
- SHA256:
  `1e9e60c937de8930f87ea62849824d15ab0efba689da8b5fa26a3ebd83095902`
- marker: `a90_android_execns_probe v93`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

## Success Criteria

One of these bounded outcomes is acceptable:

1. `IWifi.start()` returns `WifiStatus.SUCCESS`, cleanup is safe, and no
   scan/connect/link-up was executed;
2. `IWifi.start()` returns a decoded non-success `WifiStatus`, identifying the
   next missing runtime dependency;
3. the status cannot be decoded, proving the reply parser needs another repair.

Wi-Fi objective remains incomplete until native init successfully connects to
Wi-Fi and external ping passes.
