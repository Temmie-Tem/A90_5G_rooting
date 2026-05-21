# Native Init V556 Companion Plus HAL Order Plan

Date: `2026-05-21`

## Goal

V555 showed that `qmiproxy`, `ssgqmigd`, `sysmon-qmi`, and
`service-notifier` are not startable extra QMI companion targets in the
currently mounted images. V556 therefore tests the next Android-observed
boundary: combining the companion service set with the Wi-Fi HAL in one bounded
private namespace.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start a bounded helper-owned private namespace;
- start only service managers, companion daemons, Wi-Fi HAL, `cnss_diag`, and
  `cnss-daemon`;
- collect dmesg, process, network, QRTR, and runtime-surface evidence;
- cleanup all helper-owned children.

Forbidden:

- `wificond`, supplicant, hostapd start;
- `IWifi.start()` transaction;
- scan/connect/link-up;
- credential handling;
- DHCP, route changes, or external ping;
- boot partition write, reboot, or Android partition mutation.

## Helper Change

Helper v81 adds:

```text
wifi-companion-hal-order-start-only
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
vendor.wifi_hal_ext
cnss_diag
cnss-daemon
```

The mode defaults the Wi-Fi HAL target to
`/vendor/bin/hw/vendor.samsung.hardware.wifi@2.0-service` to keep the cmdv1
argument budget at 30 arguments.

## Commands

Build:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v556-a90_android_execns_probe-v81/a90_android_execns_probe
```

Deploy:

```bash
python3 scripts/revalidation/wifi_execns_helper_v81_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v556 deploy execns helper v81 only; no daemon start and no Wi-Fi bring-up" \
  run
```

Live proof:

```bash
python3 scripts/revalidation/native_wifi_companion_hal_order_v556.py \
  --apply --assume-yes \
  --approval-phrase "approve v556 companion plus HAL order start-only proof only; no wificond, no supplicant, no scan/connect/link-up and no external ping" \
  run
```

## Success Criteria

Pass if one of these states is proven:

1. combined order window produces WLFW/QMI/BDF/wlan0 readiness markers and
   cleanup is safe; or
2. all children stay observable until timeout, cleanup is safe, and readiness
   markers remain absent, proving the blocker is beyond this boundary.

Block if any helper-owned child is not proven stopped, if scan/connect/link-up
appears, or if a Wi-Fi network interface appears unexpectedly.

## Next Gate

If V556 still has no WLFW/QMI/BDF marker, the next useful boundary is not
another blind companion retry. Inspect HAL registration/runtime output and
consider a bounded `wificond` start-only proof, because Android starts
`wificond` between `cnss_diag` and `cnss-daemon`.
