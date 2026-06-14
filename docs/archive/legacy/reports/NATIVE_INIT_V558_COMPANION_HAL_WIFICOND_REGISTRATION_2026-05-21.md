# Native Init V558 Companion Plus HAL Plus Wificond Registration Report

Date: `2026-05-21`

## Goal

Determine whether the V557 11-child native private namespace is enough for the
Samsung Wi-Fi HAL to register a HIDL service before any `IWifi.start()`,
supplicant, scan/connect, or external network work.

## Result

- Decision: `v558-samsung-registration-observed`
- Pass: `True`
- Reason: Samsung Wi-Fi HAL registration observed:
  `vendor.samsung.hardware.wifi@2.0::ISehWifi/default`
- Evidence: `tmp/wifi/v558-companion-hal-wificond-registration`
- Helper: `a90_android_execns_probe v83`
- Helper SHA-256:
  `79af5542abe0c2f73641302f82b8e481654844ed983e0e4eb7ae367afb9d0111`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v83 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded 11-child helper-owned window.
- `lshal wait` was executed only as a registration query.
- `IWifi.start()`, supplicant, hostapd, scan/connect/link-up, credentials, DHCP,
  route changes, external ping, reboot, and boot partition writes were not
  executed.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Result

Key registration outputs:

```text
wifi_companion_hal_order.service_query=1
wifi_hal_micro_query.target.0.fqinstance=vendor.samsung.hardware.wifi@2.0::ISehWifi/default
wifi_hal_micro_query.target.0.exit_code=0
wifi_hal_micro_query.target.0.timed_out=0
wifi_hal_micro_query.target.0.result=service-query-pass
wifi_hal_micro_query.result=service-query-pass
wifi_hal_micro_query.reason=lshal-wait-exit-zero
wifi_hal_micro_query.matched_fqinstance=vendor.samsung.hardware.wifi@2.0::ISehWifi/default
wifi_companion_hal_order.service_query_result=0
wifi_companion_hal_order.all_postflight_safe=1
wifi_companion_hal_order.result=service-query-pass
```

Safety outputs:

```text
wifi_companion_hal_order.scan_connect_linkup=0
wifi_companion_hal_order.external_ping=0
wifi_companion_hal_order.qmi_payload=0
post-run residue: none
wifi netdev: none
```

## Dmesg Evidence

Markers that appeared:

| marker | count |
| --- | ---: |
| `cnss_diag_netlink` | 11 |
| `cnss_daemon_netlink` | 25 |

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

V558 is the first native-init proof in this sequence that observes Samsung
Wi-Fi HAL registration inside the bounded private namespace:

- V469 timed out waiting for Samsung registration with a smaller surface.
- V557 showed the fuller Android-like process order could stay clean but did
  not prove service registration.
- V558 proves `vendor.samsung.hardware.wifi@2.0::ISehWifi/default` is now
  registered under the 11-child window.

The blocker has therefore moved from "HAL does not register" to "registered HAL
has not yet been driven to firmware/netdev readiness." The next controlled
boundary is a bounded HAL start/control transaction, still before scan/connect
or credentials.

## Validation

Commands run:

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v558-a90_android_execns_probe-v83/a90_android_execns_probe

python3 -m py_compile \
  scripts/revalidation/wifi_execns_helper_v83_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_hal_wificond_registration_v558.py

python3 scripts/revalidation/wifi_execns_helper_v83_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v558 deploy execns helper v83 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_companion_hal_wificond_registration_v558.py preflight

python3 scripts/revalidation/native_wifi_companion_hal_wificond_registration_v558.py \
  --apply --assume-yes \
  --approval-phrase "approve v558 companion plus HAL plus wificond Samsung registration wait only; no IWifi.start, no supplicant, no scan/connect/link-up and no external ping" \
  run
```

Result:

```text
decision: v558-samsung-registration-observed
pass: True
reason: Samsung Wi-Fi HAL registration observed: vendor.samsung.hardware.wifi@2.0::ISehWifi/default
```

## Next Gate

Recommended V559:

1. keep the V558 11-child registered window;
2. perform one bounded pre-scan HAL start/control transaction;
3. capture firmware/netdev/readiness markers and cleanup state;
4. still block credentials, scan/connect/link-up, DHCP, routes, and external
   ping until a WLAN surface or scan-only-ready marker is proven.
