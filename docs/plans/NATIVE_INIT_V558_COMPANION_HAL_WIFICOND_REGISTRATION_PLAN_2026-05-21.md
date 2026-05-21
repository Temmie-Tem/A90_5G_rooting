# Native Init V558 Companion Plus HAL Plus Wificond Registration Plan

Date: `2026-05-21`

## Goal

V557 proved the service-manager, companion, Wi-Fi HAL, `wificond`, and CNSS
process order can remain alive and clean, but no firmware or netdev marker
appeared. V558 adds one bounded read-only registration query inside that same
window to determine whether the Samsung Wi-Fi HAL registers its HIDL service.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start the V557 11-child private namespace window;
- run `/system/bin/lshal wait` for Samsung Wi-Fi HAL fqinstances;
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

Helper v83 adds:

```text
wifi-companion-hal-wificond-lshal-wait-samsung
```

The child window remains:

```text
servicemanager
hwservicemanager
vndservicemanager
qrtr-ns
rmt_storage
tftp_server
pd-mapper
vendor.samsung.hardware.wifi@2.0-service
cnss_diag
wificond
cnss-daemon
```

After the warmup window, the helper runs `lshal wait` only for Samsung Wi-Fi
HAL registration targets. It does not call HAL methods and does not attempt
scan/connect.

## Commands

Build:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v558-a90_android_execns_probe-v83/a90_android_execns_probe
```

Deploy:

```bash
python3 scripts/revalidation/wifi_execns_helper_v83_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v558 deploy execns helper v83 only; no daemon start and no Wi-Fi bring-up" \
  run
```

Live proof:

```bash
python3 scripts/revalidation/native_wifi_companion_hal_wificond_registration_v558.py \
  --apply --assume-yes \
  --approval-phrase "approve v558 companion plus HAL plus wificond Samsung registration wait only; no IWifi.start, no supplicant, no scan/connect/link-up and no external ping" \
  run
```

## Success Criteria

Pass if one of these states is proven:

1. Samsung Wi-Fi HAL registration is observed and all helper-owned processes are
   cleaned; or
2. registration still times out but the full 11-child window is clean, proving
   that registration is still blocked before any HAL method call.

Block if cleanup is not proven, if `IWifi.start()`/scan/connect/link-up appears,
or if a Wi-Fi network interface appears unexpectedly.

## Next Gate

If Samsung registration is observed, move to a bounded `IWifi.start()` proof
before any scan/connect. If registration still times out, test whether the
missing Android legacy Wi-Fi HAL process is required.
