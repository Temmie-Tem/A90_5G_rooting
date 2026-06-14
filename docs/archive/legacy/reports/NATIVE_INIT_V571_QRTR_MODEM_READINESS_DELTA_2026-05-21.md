# Native Init V571 QRTR/Modem Readiness Delta Report

Date: `2026-05-21`

## Goal

Compare the Android QRTR/modem readiness sequence, the V570 helper v94 bounded
result, and the current native init QRTR/modem/service-notifier surfaces before
retrying Wi-Fi HAL or scan/connect work.

## Result

- Decision: `v571-modem-readiness-not-entered`
- Pass: `True`
- Reason: Android reference has QRTR/service-notifier/WLAN-PD/QMI markers, but
  current native and V570 both have `QIPCRTR` sockets `0` and no readiness
  markers.
- Evidence: `tmp/wifi/v571-qrtr-modem-readiness-delta`
- Device mutations: not executed
- Daemon start: not executed
- Wi-Fi bring-up: not executed

## Scope Confirmation

- V571 only ran read-only native commands.
- It did not start daemons, service-manager, Wi-Fi HAL, supplicant, hostapd, or
  any QMI payload.
- It did not scan, connect, link up, use credentials, request DHCP, change
  routes, ping externally, flash a boot image, reboot, or write Android
  partitions.

## Validation

```text
python3 -m py_compile scripts/revalidation/native_wifi_qrtr_modem_readiness_delta_v571.py
git diff --check -- scripts/revalidation/native_wifi_qrtr_modem_readiness_delta_v571.py \
  docs/plans/NATIVE_INIT_V571_QRTR_MODEM_READINESS_DELTA_PLAN_2026-05-21.md
python3 scripts/revalidation/native_wifi_qrtr_modem_readiness_delta_v571.py plan
python3 scripts/revalidation/native_wifi_qrtr_modem_readiness_delta_v571.py run
```

## Current Native Surface

| surface | value |
|---|---:|
| `QIPCRTR` protocol present | `true` |
| `QIPCRTR` sockets | `0` |
| `/proc/net/qrtr` present | `false` |
| `/dev/qrtr` present | `false` |
| `/sys/kernel/debug/service_notifier` present | `false` |
| `/sys/class/remoteproc` present | `false` |
| `/sys/bus/msm_subsys/devices` present | `true` |
| `/sys/bus/rpmsg/devices` present | `true` |
| active target process hits | `0` |
| Wi-Fi netdev/wiphy hits | `0` |

## Marker Delta

Android reference from V519 has:

```text
qrtr_modem_readiness_rx=1
qrtr_modem_readiness_tx=1
sysmon_qmi_ready=5
service_notifier_ready=2
wlan_pd_indication=2
qmi_server_connected=1
```

Current native has:

```text
qrtr_modem_readiness_rx=0
qrtr_modem_readiness_tx=0
sysmon_qmi_ready=0
service_notifier_ready=0
wlan_pd_indication=0
qmi_server_connected=0
cnss_daemon_wlfw_start=0
wlfw_thread=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0_event=0
```

V570 baseline remains:

```text
IWifi.start=ERROR_UNKNOWN/9
qipcrtr_sockets_window=0
qrtr_readback_service_events=0
rmt_tftp_identity_contracts_ok=True
all_postflight_safe=True
```

## Interpretation

The remaining blocker is earlier than Wi-Fi HAL scan/connect and earlier than
the `rmt_storage`/`tftp_server` identity contract:

1. Native has the `QIPCRTR` protocol registered, so the kernel address family is
   present.
2. Native has no counted `QIPCRTR` socket, no `/proc/net/qrtr`, no `/dev/qrtr`,
   and no service-notifier debugfs surface in the current state.
3. V570 starts Android-like companions and reaches `IWifi.start()`, but this
   still does not trigger QRTR modem readiness, service-notifier, WLAN-PD, CNSS
   QMI, BDF, or firmware-ready markers.
4. Android reaches QRTR modem readiness before/around `vendor.qrtr-ns` startup
   early in boot. The current native live proof starts these services much later
   after native boot, so timing/order is now the strongest suspect.

The next step should not be another same-window HAL retry. The next step should
test whether QRTR companion services must be brought up during native boot, not
minutes or hours later from an interactive helper.

## References

- Linux QRTR source tree:
  `https://codebrowser.dev/linux/linux/net/qrtr/`
- Qualcomm service-notifier kernel source:
  `https://android.googlesource.com/kernel/msm/+/android-7.1.0_r0.2/drivers/soc/qcom/service-notifier.c`
- Qualcomm sysmon kernel configuration:
  `https://cateee.net/lkddb/web-lkddb/QCOM_SYSMON.html`

## Next Gate

V572 should be a boot-time companion timing plan:

1. identify the minimal native init hook point after vendor/system namespace and
   SELinux/property readiness, but before any Wi-Fi HAL start;
2. start only `qrtr-ns`, `rmt_storage`, `tftp_server`, `pd-mapper`, `cnss_diag`,
   and `cnss-daemon` with the V570 identity contracts;
3. capture early boot QRTR/service-notifier/WLAN-PD/QMI/BDF/FW markers for a
   bounded window;
4. preserve rollback through the existing native/TWRP boot image path;
5. keep scan/connect/link-up blocked until native boot produces QRTR/QMI/BDF or
   `wlan0` evidence.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.
