# Native Init V571 QRTR/Modem Readiness Delta Plan

Date: `2026-05-21`

## Goal

V570 repaired the concrete `rmt_storage`/`tftp_server` Android runtime identity
mismatch, but `IWifi.start()` still returned `ERROR_UNKNOWN/9`, WLFW QRTR
readback had zero service events, and `QIPCRTR` sockets stayed `0`.

V571 is a read-only delta classifier that compares:

1. the existing Android QRTR/modem sequence from V519;
2. the V570 helper v94 bounded live result;
3. current native init QRTR, service-notifier, remoteproc/RPMSG, and modem
   readiness surfaces.

The intent is to avoid another blind HAL retry and decide whether the next live
change should target timing/order, service-notifier/sysmon, or a deeper modem
remoteproc/subsystem surface.

## Non-Goals

- no daemon or service start;
- no QMI payload;
- no Wi-Fi HAL start;
- no supplicant or hostapd;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent install.

## Reference Basis

- Linux QRTR is the kernel transport surface for Qualcomm IPC router sockets.
- Qualcomm service-notifier is kernel-side QMI/service-registry logic and
  exposes debugfs hooks in the referenced msm kernel source.
- Qualcomm sysmon is a QMI/RPMSG-facing subsystem-monitor component used around
  modem/DSP subsystem state.

References:

- <https://android.googlesource.com/kernel/msm/+/android-7.1.0_r0.2/drivers/soc/qcom/service-notifier.c>
- <https://codebrowser.dev/linux/linux/net/qrtr/>
- <https://cateee.net/lkddb/web-lkddb/QCOM_SYSMON.html>

## Implementation

Files:

- `scripts/revalidation/native_wifi_qrtr_modem_readiness_delta_v571.py`

Inputs:

- `tmp/wifi/v519-android-native-qrtr-modem-delta/manifest.json`
- `tmp/wifi/v570-companion-dual-hal-wificond-rmt-tftp-identity/manifest.json`

Read-only native surfaces:

- `/proc/net/protocols`
- `/proc/net/qrtr`
- `/proc/net/netlink`
- `/proc/net/dev`
- `/dev/qrtr`
- `/dev/wlan`
- `/sys/kernel/debug/service_notifier`
- `/sys/class/remoteproc`
- `/sys/bus/msm_subsys/devices`
- `/sys/bus/rpmsg/devices`
- `/sys/module/*qcom*`, `*qrtr*`, `*cnss*`, `*icnss*`
- filtered `dmesg`

## Classification Criteria

Acceptable outcomes:

1. Current native dmesg now contains QMI/FW readiness markers: stop and rerun a
   bounded `IWifi.start()` proof before scan.
2. Native and V570 both still have `QIPCRTR` sockets `0`, while Android has the
   QRTR/service-notifier/WLAN-PD/QMI sequence: classify as modem readiness not
   entered and focus the next live change on timing or service-notifier/sysmon.
3. Native sees modem QRTR readiness but not CNSS QMI: classify as
   service-notifier/sysmon/CNSS ordering gap.
4. Active target processes or Wi-Fi netdev exist: stop and cleanup/classify
   before further live work.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.
