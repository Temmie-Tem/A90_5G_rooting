# Native Init V557 Companion Plus HAL Plus Wificond Order Plan

Date: `2026-05-21`

## Goal

V556 proved that service managers, QRTR/RMT/TFTP/PD companions, Samsung Wi-Fi
HAL, `cnss_diag`, and `cnss-daemon` can coexist in one bounded native private
namespace, but still do not produce WLFW/QMI/BDF/wlan0 readiness markers. V557
tests the next Android-observed framework boundary by adding `wificond` to the
same start-only window.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start a bounded helper-owned private namespace;
- start only service managers, companion daemons, Wi-Fi HAL, `cnss_diag`,
  `wificond`, and `cnss-daemon`;
- apply the Android-observed `wificond` identity contract;
- collect dmesg, process, network, QRTR, runtime-surface, stdout, and stderr
  evidence;
- cleanup all helper-owned children.

Forbidden:

- supplicant or hostapd start;
- `IWifi.start()` transaction;
- scan/connect/link-up;
- credential handling;
- DHCP, route changes, or external ping;
- boot partition write, reboot, or Android partition mutation.

## Helper Change

Helper v82 adds:

```text
wifi-companion-hal-wificond-order-start-only
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
vendor.samsung.hardware.wifi@2.0-service
cnss_diag
wificond
cnss-daemon
```

`wificond` is executed from `/system/bin/wificond` with SELinux exec context
`u:r:wificond:s0`, uid/gid `wifi`, groups `wifi`, `net_raw`, and `net_admin`,
and `CAP_NET_RAW`/`CAP_NET_ADMIN`. This matches the Android init contract while
still avoiding supplicant, scan, credentials, network configuration, and
external traffic.

## Commands

Build:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v557-a90_android_execns_probe-v82/a90_android_execns_probe
```

Deploy:

```bash
python3 scripts/revalidation/wifi_execns_helper_v82_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v557 deploy execns helper v82 only; no daemon start and no Wi-Fi bring-up" \
  run
```

Live proof:

```bash
python3 scripts/revalidation/native_wifi_companion_hal_wificond_order_v557.py \
  --apply --assume-yes \
  --approval-phrase "approve v557 companion plus HAL plus wificond order start-only proof only; no supplicant, no scan/connect/link-up and no external ping" \
  run
```

## Success Criteria

Pass if one of these states is proven:

1. the wificond-inclusive order window produces WLFW/QMI/BDF/wlan0 readiness
   markers and cleanup is safe; or
2. all children stay observable until timeout, cleanup is safe, and readiness
   markers remain absent, proving the blocker is beyond simple process order
   and `wificond` start-only presence.

Block if any helper-owned child is not proven stopped, if supplicant/hostapd
starts, if scan/connect/link-up appears, or if a Wi-Fi network interface appears
unexpectedly.

## Next Gate

If V557 still has no WLFW/QMI/BDF marker, the next useful boundary is no longer
simple process replay. Inspect HAL/wificond stderr and service registration,
then move toward a bounded `IWifi.start()` or scan-only surface only after the
registration path is understood.
