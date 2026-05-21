# Native Init V557 Companion Plus HAL Plus Wificond Order Report

Date: `2026-05-21`

## Goal

Test whether adding Android's `wificond` boundary to the already-safe V556
service-manager, companion, Wi-Fi HAL, `cnss_diag`, and `cnss-daemon` window is
enough to produce native WLFW/QMI/BDF/wlan0 readiness markers before any
supplicant, scan/connect, or external network work.

## Result

- Decision: `v557-wificond-order-no-fw-marker`
- Pass: `True`
- Reason: companion plus HAL plus `wificond` order window stayed alive and
  cleaned, but no WLFW/QMI/BDF/wlan0 marker appeared.
- Evidence: `tmp/wifi/v557-companion-hal-wificond-order`
- Helper: `a90_android_execns_probe v82`
- Helper SHA-256:
  `643a40aa3e0bd2108f5417e30c704d490ec1c237cadfd005650732621f82a881`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v82 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only a bounded helper-owned start-only window.
- `wificond` was included, but supplicant, hostapd, `IWifi.start()`,
  scan/connect/link-up, credentials, DHCP, route changes, external ping,
  reboot, and boot partition writes were not executed.
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
wificond
cnss-daemon
```

Key helper outputs:

```text
wifi_companion_hal_order.wificond=1
wifi_companion_hal_order.supplicant=0
wifi_companion_hal_order.hostapd=0
wifi_companion_hal_order.scan_connect_linkup=0
wifi_companion_hal_order.credentials=0
wifi_companion_hal_order.dhcp_routing=0
wifi_companion_hal_order.external_ping=0
wifi_companion_hal_order.qmi_payload=0
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
| binder one-way unsupported ioctl noise | 4 |

Readiness markers that did not appear:

| marker | count |
| --- | ---: |
| `qmi_server_connected` | 0 |
| `qrtr_modem_readiness` | 0 |
| `wlfw_start` | 0 |
| `wlfw_thread` | 0 |
| `bdf_regdb` | 0 |
| `bdf_bdwlan` | 0 |
| `wlan_fw_ready` | 0 |
| `wlan0_event` | 0 |
| `wma_service_ready` | 0 |

## Interpretation

V557 moves the blocker forward again:

- The service-manager trio, six companion targets, Samsung Wi-Fi HAL,
  `cnss_diag`, `wificond`, and `cnss-daemon` can coexist in one bounded native
  private namespace.
- `wificond` start-only presence is not enough to trigger firmware readiness,
  QMI server connection, BDF loading, or a `wlan0` surface.
- The gap is now likely at service registration/control flow, `IWifi.start()`,
  or another framework transaction rather than at basic process presence or
  Android init ordering.

This means blind companion retries are low-value. The next step should inspect
HAL/wificond registration surfaces and only then move into a bounded start or
scan-only gate.

## Validation

Commands run:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v557-a90_android_execns_probe-v82/a90_android_execns_probe

python3 -m py_compile \
  scripts/revalidation/wifi_execns_helper_v82_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_hal_wificond_order_v557.py

python3 scripts/revalidation/wifi_execns_helper_v82_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v557 deploy execns helper v82 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_companion_hal_wificond_order_v557.py preflight

python3 scripts/revalidation/native_wifi_companion_hal_wificond_order_v557.py \
  --apply --assume-yes \
  --approval-phrase "approve v557 companion plus HAL plus wificond order start-only proof only; no supplicant, no scan/connect/link-up and no external ping" \
  run
```

Result:

```text
decision: v557-wificond-order-no-fw-marker
pass: True
reason: companion plus HAL plus wificond order window stayed alive and cleaned, but no WLFW/QMI/BDF/wlan0 marker appeared
```

## Next Gate

Recommended V558:

1. inspect V557 HAL and `wificond` stdout/stderr plus binder/hwbinder
   registration surfaces;
2. classify whether `IWifi.start()` is the first missing transaction or whether
   a framework/service registration dependency is still absent;
3. keep credentials, scan/connect/link-up, DHCP, routing, and external ping
   blocked until a scan-only or IWifi-ready marker is proven.
