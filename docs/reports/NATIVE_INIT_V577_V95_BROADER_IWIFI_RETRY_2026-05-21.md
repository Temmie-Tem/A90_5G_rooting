# Native Init V577 V95 Broader IWifi Retry Report

Date: `2026-05-21`

## Goal

Retry the broader bounded service-manager + companion + dual-HAL + `wificond`
+ `IWifi.start()` window using the V95 init-root contracts for `rmt_storage`
and `tftp_server`.

## Result

- Decision: `v577-v95-broader-not-sufficient`
- Pass: `True`
- Reason: V95 init-root contracts applied, but `IWifi.start()` still returned
  `ERROR_UNKNOWN/9` and `QIPCRTR` sockets remained `0`.
- Evidence: `tmp/wifi/v577-v95-broader-iwifi-retry`
- Device mutations: executed only bounded process start/cleanup window
- Daemon/HAL start: executed only the bounded proof window
- Wi-Fi bring-up: not executed

## Scope Confirmation

- V577 started only the already-modeled bounded service-manager, companion,
  dual-HAL, `wificond`, and `IWifi.start()` proof window.
- It did not send QMI payloads.
- It did not start supplicant or hostapd.
- It did not scan, connect, link up, use credentials, request DHCP, change
  routes, ping externally, flash a boot image, reboot, write Android
  partitions, mutate firmware, write rfkill, or bind/unbind drivers.
- Post-run cleanup was safe and current native status is normal on
  `A90 Linux init 0.9.61 (v319)`.

## Validation

```text
python3 -m py_compile scripts/revalidation/native_wifi_v95_broader_iwifi_retry_v577.py
python3 scripts/revalidation/native_wifi_v95_broader_iwifi_retry_v577.py \
  --v490-manifest tmp/wifi/v575-v490-policy-load-run-after-layout/manifest.json \
  preflight
python3 scripts/revalidation/native_wifi_v95_broader_iwifi_retry_v577.py \
  --v490-manifest tmp/wifi/v575-v490-policy-load-run-after-layout/manifest.json \
  --approval-phrase "approve v577 v95 service-manager dual-hal iwifi start-only retry only; no QMI payload, no supplicant, no scan/connect/link-up and no external ping" \
  --apply --assume-yes run
python3 scripts/revalidation/a90ctl.py status
```

## Live Evidence

V95 init-root contract validation passed:

| child | contract | uid | gid | capability mode | preexec | SELinux exec | match |
|---|---|---:|---:|---|---|---|---:|
| `rmt_storage` | `rmt_storage-init-root` | `0` | `0` | `android-init-root` | `pass` | `u:r:vendor_rmt_storage:s0` | `1` |
| `tftp_server` | `tftp_server-init-root` | `0` | `0` | `android-init-root` | `pass` | `u:r:vendor_rfs_access:s0` | `1` |

The Wi-Fi HAL start path still failed before scan/connect:

```text
helper_result=iwifi-transaction-failed
iwifi_start_wifi_status_name=ERROR_UNKNOWN
iwifi_start_wifi_status_code=9
qrtr_readback_service_events=0
qrtr_readback_qmi_attempted=0
qipcrtr_sockets_before=0
qipcrtr_sockets_after_spawn=0
qipcrtr_sockets_window=0
qipcrtr_sockets_after_cleanup=0
all_postflight_safe=True
scan_connect_linkup=False
external_ping=False
```

Dmesg readiness stayed absent:

```text
qmi_server_connected=0
qrtr=0
qrtr_modem_readiness=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0_event=0
wlfw_start=0
wlfw_thread=0
```

## Interpretation

V577 closes the major ambiguity left after V575/V576: the V95 init-root repair
does not become sufficient when replayed with service-manager, dual HAL,
`wificond`, and `IWifi.start()`.

The remaining blocker is still before scan/connect. Current evidence rules out:

1. pre-dropping `rmt_storage`/`tftp_server` as the remaining cause;
2. missing bounded service-manager/HAL ordering as a sufficient fix;
3. raw `IWifi.start()` transport as the immediate blocker;
4. a safe reason to attempt credentials, scan/connect, DHCP, routing, or
   external ping now.

The next useful work should classify why the QRTR/modem path is not entering
the Android-equivalent readiness state even under the broader V95 window.

## Next Gate

V578 should focus on Android-vs-native modem/QRTR dependency surfaces that are
still missing in native:

1. compare Android and native service-notifier/sysmon/subsystem/rpmsg/qmi
   surfaces with V577 as the native baseline;
2. identify whether a specific vendor service, node, mount, property, binder
   service, or subsystem trigger is missing before `cnss-daemon` can reach WLFW;
3. keep Wi-Fi scan/connect blocked until at least one of these appears:
   `qmi_server_connected`, BDF request, WLFW thread/start marker, `wlan0`, or
   a successful `IWifi.start()`.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.
