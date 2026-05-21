# Native Init V569 HAL ERROR_UNKNOWN Dependency Plan

Date: `2026-05-21`

## Goal

V568 proved that raw hwbinder mechanics are now working: the helper reaches
`android.hardware.wifi@1.0::IWifi/default`, retains the returned handle, calls
`IWifi.start()`, and decodes a valid HIDL `WifiStatus`. The HAL still returns
`WifiStatusCode.ERROR_UNKNOWN/9` and no WLAN/PHY, QRTR/QMI, BDF, or WLFW
readiness marker appears.

V569 classifies that `ERROR_UNKNOWN` path by adding a bounded WLFW QRTR
nameservice readback to the same companion/HAL/`wificond` window and by
summarizing the already-captured runtime surfaces.

## Non-Goals

- no QMI payload;
- no supplicant or hostapd start;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Reference Basis

- Linux QRTR is the Qualcomm IPC Router transport used to communicate with
  services from other hardware blocks, and service lookup requires a userspace
  service-listing daemon.
- Qualcomm platform boot-essential userspace commonly includes QRTR/RMTFS/TFTP
  components, and tqftpserv is a TFTP server over `AF_QIPCRTR`.
- The current A90 native proof already starts Android vendor companions
  `qrtr-ns`, `rmt_storage`, `tftp_server`, `pd-mapper`, `cnss_diag`, and
  `cnss-daemon`, but V568 still showed `QIPCRTR` sockets at `0` and no WLFW
  readiness.

References:

- <https://cateee.net/lkddb/web-lkddb/QRTR.html>
- <https://raw.githubusercontent.com/qualcomm-linux/meta-qcom/master/recipes-bsp/packagegroups/packagegroup-qcom.bb>
- <https://raw.githubusercontent.com/qualcomm-linux/meta-qcom/master/recipes-support/qrtr/qrtr_1.2.bb>
- <https://sources.debian.org/src/tqftpserv/1.1-4/tqftpserv.c>
- <https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/types.hal>

## Implementation

Files:

- `scripts/revalidation/native_wifi_companion_dual_hal_wificond_error_unknown_dependency_v569.py`

Helper artifact:

- required marker: `a90_android_execns_probe v93`
- required SHA256:
  `1e9e60c937de8930f87ea62849824d15ab0efba689da8b5fa26a3ebd83095902`
- required mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

V569 reuses helper v93 and adds only `--allow-qrtr-ns-readback` to the V568
bounded helper command. No C helper rebuild is required.

## Classification Criteria

Acceptable bounded outcomes:

1. `IWifi.start()` returns `SUCCESS`: stop before scan/connect and move to a
   separate scan-only gate.
2. `IWifi.start()` returns `ERROR_UNKNOWN`, WLFW QRTR readback has no service
   events, and `QIPCRTR` socket count remains `0`: classify as missing
   modem/QRTR/WLFW readiness dependency.
3. `IWifi.start()` returns `ERROR_UNKNOWN`, but WLFW service events appear:
   classify as non-QRTR runtime dependency, then inspect firmware/BDF,
   `/data/vendor/wifi`, HAL logs, and CNSS logs before scan/connect.
4. Cleanup is not proven safe: stop and recover before further live work.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.
