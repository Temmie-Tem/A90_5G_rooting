# Native Init V465 IWifi.start Contract

Date: 2026-05-20

## Summary

V465 fixed the next native-init Wi-Fi control contract after V464.  The result
is **not** a Wi-Fi bring-up pass.  It proves the next executable step must be a
small helper-owned raw hwbinder primitive that performs:

1. bounded V464-style private runtime start;
2. `IServiceManager.get(android.hardware.wifi@1.0::IWifi, default)`;
3. exactly one `IWifi.start()` transaction;
4. WLAN surface snapshots;
5. full cleanup.

Decision:

```text
v465-iwifi-start-contract-ready-raw-hwbinder-next
```

## Current Device State

- Native version: `A90 Linux init 0.9.61 (v319)`.
- V464 input: `v464-native-wlan-surface-not-observed`.
- Current native WLAN surface: still absent.
- Credentials, scan/connect, DHCP, route changes, and external packets:
  not executed.

## Contract

The pinned HIDL control contract is:

| Item | Value |
| --- | --- |
| Service manager descriptor | `android.hidl.manager@1.0::IServiceManager` |
| Service manager instance | `manager` |
| Service manager method | `get(string fqName, string name)` |
| Service manager transaction code | `1` |
| Wi-Fi HAL descriptor | `android.hardware.wifi@1.0::IWifi` |
| Wi-Fi HAL instance | `default` |
| Wi-Fi HAL method | `start() generates (WifiStatus status)` |
| Wi-Fi HAL transaction code | `3` |

The `IWifi.start()` call remains bounded and pre-credential.  It is only a
surface-creation probe.

## Strategy Result

| Strategy | Result | Reason |
| --- | --- | --- |
| Generated HIDL client | Not available | `hidl-gen` and generated `IWifi` C++ headers are not present in this repo/build environment. |
| Existing Android tool | Not usable | `lshal` can enumerate/wait/status HIDL services, but it is not an `IWifi.start()` invoker. `cmd`/`svc` require Android framework services and do not satisfy the native-init HAL-only path. |
| Raw hwbinder client | Selected next | It can stay in native init, avoid framework scan/connect paths, and call exactly `IWifi.start()` once. |

## Evidence

- Plan evidence:
  `tmp/wifi/v465-iwifi-start-contract-plan-20260520-234757/`
- Preflight evidence:
  `tmp/wifi/v465-iwifi-start-contract-preflight-20260520-234757/`

Key preflight checks:

- `native-clean`: pass
- `helper-v31-context`: pass
- `v464-surface-input`: pass
- `wifi-surface-still-absent`: pass
- `iwifi-contract-explicit`: pass
- `raw-hwbinder-strategy`: next

## Implementation

Added:

```text
scripts/revalidation/wifi_iwifi_start_contract_v465.py
```

The script is fail-closed:

- `plan`: no device command.
- `preflight`: read-only native commands only.
- no daemon start;
- no Wi-Fi HAL start;
- no `IWifi.start`;
- no credentials;
- no packets.

## Reference Basis

- AOSP `IWifi.hal` defines `start()` as the setup call that makes the Wi-Fi HAL
  usable and returns `WifiStatus`.
  <https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/IWifi.hal>
- AOSP HIDL service manager defines `get(string fqName, string name)` for
  obtaining the service handle.
  <https://android.googlesource.com/platform/system/libhidl/+/refs/heads/android12L-tests-dev/transport/manager/1.0/IServiceManager.hal>
- AOSP HIDL generated C++ dispatch uses stable serial transaction IDs for
  interface methods.
  <https://android.googlesource.com/platform/system/tools/hidl/+/refs/heads/main/generateCpp.cpp>
- AOSP `Parcel::writeInterfaceToken` writes the interface token used by the
  hwbinder transaction.
  <https://android.googlesource.com/platform/system/libhwbinder/+/7919fa0d4240e22e1e0c88b99cb6b6b921646d7e/Parcel.cpp>

## Next

V466 should implement:

```text
a90_android_execns_probe v32
mode: wifi-iwifi-start-surface
allow flag: --allow-iwifi-start-only
runner: native_iwifi_start_surface_v466.py
```

The V466 live gate should remain blocked from SSID/password, scan/connect,
DHCP, routes, and external ping until a native `wlan0`/`phy*`/Wi-Fi rfkill
surface appears and postflight cleanup is clean.
