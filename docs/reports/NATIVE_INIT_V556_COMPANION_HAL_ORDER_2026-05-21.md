# Native Init V556 Companion Plus HAL Order Report

Date: `2026-05-21`

## Goal

Test whether Android-like ordering of service managers, QRTR/RMT/TFTP/PD
companions, Samsung Wi-Fi HAL, `cnss_diag`, and `cnss-daemon` is enough to
produce native WLFW/QMI/BDF/wlan0 readiness markers before any scan/connect
work.

## Result

- Decision: `v556-order-no-fw-marker`
- Pass: `True`
- Reason: combined companion plus HAL order window stayed alive and cleaned,
  but no WLFW/QMI/BDF/wlan0 marker appeared.
- Evidence: `tmp/wifi/v556-companion-hal-order`
- Helper: `a90_android_execns_probe v81`
- Helper SHA-256:
  `b5b72889bca65a69523946afa914979f0ca8b921809f44aebb6de30debcc41c9`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v81 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only a bounded helper-owned start-only window.
- `wificond`, supplicant, hostapd, `IWifi.start()`, scan/connect/link-up,
  credentials, DHCP, route changes, external ping, reboot, and boot partition
  writes were not executed.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Window

Child order:

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
cnss-daemon
```

All children were observable and postflight-safe:

```text
wifi_companion_hal_order.timed_out=1
wifi_companion_hal_order.all_observable_at_timeout=1
wifi_companion_hal_order.all_postflight_safe=1
wifi_companion_hal_order.result=order-window-pass
```

The separate postflight check also showed:

```text
post-run residue: none
wifi netdev: none
```

## Dmesg Evidence

Markers that appeared:

| marker | count |
| --- | ---: |
| `cnss_diag_netlink` | 11 |
| `cnss_daemon_netlink` | 25 |
| `rmt_storage` | 2 |
| binder one-way unsupported ioctl noise | 2 |

Readiness markers that did not appear:

| marker | count |
| --- | ---: |
| `qmi_server_connected` | 0 |
| `wlfw_start` | 0 |
| `wlfw_thread` | 0 |
| `bdf_regdb` | 0 |
| `bdf_bdwlan` | 0 |
| `wlan_fw_ready` | 0 |
| `wlan0_event` | 0 |

## Interpretation

V556 moves the blocker forward:

- The six required companions, service-manager trio, Samsung Wi-Fi HAL,
  `cnss_diag`, and `cnss-daemon` can coexist in one bounded native private
  namespace.
- Cleanup remains safe even with ten children.
- The Wi-Fi HAL process staying alive is not enough to trigger WLFW/QMI/BDF.
- The blocker is now likely at HAL registration/control flow or the next
  Android framework boundary, not at simple process ordering or missing
  `qmiproxy`/`ssgqmigd` binaries.

This matches the Android timing model: Android starts `wificond` between
`cnss_diag` and `cnss-daemon`. Native still has not reproduced that boundary.

## Validation

Commands run:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v556-a90_android_execns_probe-v81/a90_android_execns_probe

python3 -m py_compile \
  scripts/revalidation/wifi_execns_helper_v81_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_hal_order_v556.py

python3 scripts/revalidation/wifi_execns_helper_v81_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v556 deploy execns helper v81 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_companion_hal_order_v556.py preflight

python3 scripts/revalidation/native_wifi_companion_hal_order_v556.py \
  --apply --assume-yes \
  --approval-phrase "approve v556 companion plus HAL order start-only proof only; no wificond, no supplicant, no scan/connect/link-up and no external ping" \
  run
```

Result:

```text
decision: v556-order-no-fw-marker
pass: True
reason: combined companion plus HAL order window stayed alive and cleaned, but no WLFW/QMI/BDF/wlan0 marker appeared
```

## Next Gate

Recommended V557:

1. inspect V556 HAL stdout/stderr, service registration, and runtime surface;
2. compare Android timing for `wificond` relative to `cnss_diag` and
   `cnss-daemon`;
3. plan a bounded `wificond` start-only proof only if its runtime prerequisites
   are clear;
4. still block credentials, scan/connect/link-up, DHCP, routing, and external
   ping until a scan-only or IWifi-ready marker is proven.
