# Native Init V581 ICNSS Order Gap Classifier

- date: `2026-05-22 KST`
- objective: compare Android boot-complete Wi-Fi/ICNSS order with latest native V580 evidence before any more live retry
- status: `classified`; Wi-Fi external ping is **not** complete

## Scope

- Host-only comparison.
- Android reference: `tmp/wifi/v206-android-icnss-cnss-map/android/commands/dmesg-wifi-cnss-tail.txt`.
- Native reference:
  - `tmp/wifi/v580-v579-postflight-icnss/native/dmesg.txt`
  - `tmp/wifi/v579-v95-companion-driver-state/native/v579-helper-run.txt`
- Context manifests:
  - `tmp/wifi/v519-android-native-qrtr-modem-delta/manifest.json`
  - `tmp/wifi/v571-qrtr-modem-readiness-delta/manifest.json`
  - `tmp/wifi/v580-v579-postflight-icnss/manifest.json`

## Guardrails

- No device command.
- No daemon start.
- No qcwlanstate write.
- No `IWifi.start()` retry.
- No scan/connect/link-up/DHCP/routing.
- No external ping.

## Implementation

- `scripts/revalidation/native_wifi_icnss_order_gap_v581.py`
  - parses Android and native dmesg/helper transcripts with the same marker table
  - treats helper transcript child-start evidence as native start evidence
  - keeps actual readiness markers restricted to dmesg/QMI/BDF/FW/netdev lines
  - groups missing native markers by stage

## V581 Result

Command result:

```text
decision: v581-native-missing-modem-qrtr-readiness-before-qcwlanstate
pass: True
reason: Android reaches QRTR modem readiness and service-notifier/WLAN-PD before QMI/BDF/FW-ready; native reaches qcwlanstate/CNSS netlink but lacks those modem companion readiness markers
next: plan V582 around QRTR modem readiness/service-notifier/sysmon gap; keep qcwlanstate/IWifi/scan/connect blocked
```

Evidence:

- `tmp/wifi/v581-icnss-order-gap/`

## Stage Gaps

| stage | missing native markers |
| --- | --- |
| storage | `firmware_mounts` |
| qrtr-modem | `qrtr_modem_readiness_rx`, `qrtr_modem_readiness_tx` |
| modem-companion | `sysmon_qmi_ready`, `service_notifier_ready`, `wlan_pd_indication` |
| wlfw | `cnss_daemon_wlfw_start`, `wlfw_thread`, `qmi_server_connected` |
| firmware | `bdf_regdb`, `bdf_bdwlan` |
| ready | `wlan_fw_ready` |

Native now has these important markers:

```text
wlan_driver_load=yes
wlan_state_initialized=yes
qrtr_ns_start=yes
cnss_diag_start=yes
cnss_diag_netlink=yes
cnss_daemon_start=yes
cnss_daemon_netlink=yes
wifi_turning_on=yes
timed_out=yes
modules_not_initialized=yes
```

So the blocker is no longer “we did not start QRTR/CNSS/HAL companions at all”. The blocker is specifically that native does not enter the modem QRTR/service-notifier/WLAN-PD/WLFW readiness sequence that Android reaches before firmware-ready.

## Android Order Reference

Android reaches the successful path in this order:

```text
firmware_mounts @ 4.834s
wlan_driver_load @ 5.855s
wlan_state_initialized @ 5.862s
qrtr_modem_readiness_rx @ 6.356s
qrtr_ns_start @ 6.957s
qrtr_modem_readiness_tx @ 7.001s
sysmon_qmi_ready @ 7.006s
service_notifier_ready @ 7.028s
cnss_diag_start @ 7.808s
cnss_diag_netlink @ 7.884s
cnss_daemon_start @ 8.112s
cnss_daemon_netlink @ 8.165s
cnss_daemon_wlfw_start @ 8.295s
wlfw_thread @ 8.324s
wlan_pd_indication @ 9.421s
qmi_server_connected @ 9.423s
bdf_regdb @ 9.496s
bdf_bdwlan @ 9.511s
wifi_turning_on @ 12.572s
wlan_fw_ready @ 14.571s
wlan0_event @ 14.725s
```

Native reaches only:

```text
wlan_driver_load
wlan_state_initialized
qrtr_ns_start
cnss_diag_start
cnss_diag_netlink
cnss_daemon_start
cnss_daemon_netlink
wifi_turning_on
timed_out
modules_not_initialized
```

## Interpretation

- V579/V580 already proved `/dev/wlan` exists and qcwlanstate `ON` reaches the driver.
- V581 proves native also starts the local QRTR/CNSS companion stack far enough for `cnss_diag` and `cnss-daemon` netlink.
- The missing transition is earlier/lower than scan/connect and still below the useful `IWifi.start()` retry point.
- Android receives modem QRTR readiness and service-notifier WLAN-PD indication before QMI/BDF/FW-ready; native does not.
- Re-running qcwlanstate `ON` or `IWifi.start()` without changing this layer is expected to reproduce the V579/V580 `EINVAL` timeout.

## Source Interpretation

The QCACLD qcwlanstate source accepts `ON`, waits for WLAN driver load completion if the driver is not loaded, and can return `-EINVAL` on timeout. That aligns with native V580: `ON` reaches the driver, but the lower readiness sequence never reaches QMI/BDF/FW-ready.

Source:

- `wlan_hdd_main.c` in Android kernel/msm QCACLD: https://android.googlesource.com/kernel/msm/+/android-msm-wahoo-4.4-oreo-m4/drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c

## Next Gate

Recommended V582:

1. Build a read-only service/binary/source classifier for the missing Android modem companion path:
   - `sysmon-qmi`
   - `service-notifier`
   - WLAN-PD indication path
   - QRTR modem readiness RX/TX
2. Confirm whether those are userland binaries, kernel-triggered services, init classes, or modem-side events.
3. Keep qcwlanstate retry, `IWifi.start()`, scan, connect, and external ping blocked until the missing QRTR/modem readiness path is explained.
