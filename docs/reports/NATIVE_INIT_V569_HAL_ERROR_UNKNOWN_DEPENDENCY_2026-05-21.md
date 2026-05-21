# Native Init V569 HAL ERROR_UNKNOWN Dependency Report

Date: `2026-05-21`

## Goal

Classify the V568 `IWifi.start()` failure by checking whether WLFW is visible
through QRTR while the bounded Android-like companion, dual-HAL, CNSS, and
`wificond` window is alive.

## Result

- Decision: `v569-error-unknown-qrtr-wlfw-missing`
- Pass: `True`
- Reason: `IWifi.start()` returned `WifiStatusCode.ERROR_UNKNOWN/9`; WLFW QRTR
  readback returned no service events and `QIPCRTR` socket count stayed `0`.
- Evidence:
  `tmp/wifi/v569-companion-dual-hal-wificond-error-unknown-dependency`
- Helper: `a90_android_execns_probe v93`
- Helper SHA-256:
  `1e9e60c937de8930f87ea62849824d15ab0efba689da8b5fa26a3ebd83095902`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v93 was already present and passed preflight.
- The live proof started only the bounded companion, service-manager, dual-HAL,
  CNSS, and `wificond` window.
- The proof added only WLFW QRTR nameservice readback for service `69`,
  instances `0` and `1`.
- No QMI payload was sent.
- The proof did not run supplicant, hostapd, scan/connect/link-up, credentials,
  DHCP, route changes, external ping, reboot, or boot partition writes.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Live Evidence

```text
iwifi_start.service_token_wire=cstring
iwifi_start.service_retained=1
iwifi_start.start.reply.status_name=OK
iwifi_start.start.wifi_status.decoded=1
iwifi_start.start.wifi_status.code=9
iwifi_start.start.wifi_status.name=ERROR_UNKNOWN
iwifi_start.result=transaction-failed
wifi_companion_hal_order.surface_after_iwifi_start.wlan_count=0
wifi_companion_hal_order.surface_after_iwifi_start.phy_count=0
wifi_companion_hal_order.all_postflight_safe=1
```

QRTR/WLFW evidence:

```text
qipcrtr_sockets: before=0 after_spawn=0 window=0 cleanup=0
wifi_companion_qrtr_readback.case_0.service=69
wifi_companion_qrtr_readback.case_0.instance=0
wifi_companion_qrtr_readback.case_0.readback.service_events=0
wifi_companion_qrtr_readback.case_0.readback.end_of_list=1
wifi_companion_qrtr_readback.case_0.qmi_attempted=0
wifi_companion_qrtr_readback.case_1.service=69
wifi_companion_qrtr_readback.case_1.instance=1
wifi_companion_qrtr_readback.case_1.readback.service_events=0
wifi_companion_qrtr_readback.case_1.readback.end_of_list=1
wifi_companion_qrtr_readback.case_1.qmi_attempted=0
```

Readiness marker counts stayed at zero:

```text
qmi_server_connected=0
qrtr_modem_readiness=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
```

## Runtime Surface

```text
data_vendor_wifi_private=1
data_vendor_wifi_sockets_private=1
wlan0_socket_private=0
sys_wlan0_private=0
```

The bounded process window did create ordinary process socket FDs, but the
kernel `QIPCRTR` protocol summary still reported zero sockets across the
window. This keeps the blocker on modem/QRTR/WLFW readiness rather than on raw
hwbinder transport, `IWifi` handle lifetime, or `/data/vendor/wifi` directory
materialization.

## Interpretation

V569 narrows the blocker further:

1. raw hwbinder transport works;
2. `IWifi.start()` reaches the HAL and returns a decoded HAL status;
3. the HAL returns `ERROR_UNKNOWN/9`;
4. WLFW service lookup over QRTR returns end-of-list with no service events;
5. no QMI/BDF/WLFW readiness marker appears;
6. no WLAN/PHY surface appears.

The next step should not be scan/connect. The next step should compare Android
boot and native init for QRTR/modem readiness and identify which modem-side or
QRTR service state is missing before the Wi-Fi HAL can start successfully.

## References

- Linux QRTR kernel support:
  `https://cateee.net/lkddb/web-lkddb/QRTR.html`
- Qualcomm `qrtr` recipe:
  `https://raw.githubusercontent.com/qualcomm-linux/meta-qcom/master/recipes-support/qrtr/qrtr_1.2.bb`
- Qualcomm boot-essential userspace package group:
  `https://raw.githubusercontent.com/qualcomm-linux/meta-qcom/master/recipes-bsp/packagegroups/packagegroup-qcom.bb`
- `tqftpserv` QRTR socket usage:
  `https://sources.debian.org/src/tqftpserv/1.1-4/tqftpserv.c`
- AOSP `WifiStatusCode`:
  `https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/types.hal`

## Next Gate

V570 should be an Android-vs-native QRTR/modem readiness delta. It should
capture, without Wi-Fi scan/connect:

1. Android `/proc/net/qrtr`, `QIPCRTR` socket count, and WLFW service presence;
2. native `/proc/net/qrtr` and WLFW readback under the same timing window;
3. modem/rmt/tftp/pd-mapper logs and process FDs;
4. firmware/BDF file paths referenced by the running Android stack;
5. the minimum missing native surface before retrying `IWifi.start()`.
