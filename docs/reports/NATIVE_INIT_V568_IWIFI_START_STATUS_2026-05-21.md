# Native Init V568 IWifi.start Status Report

Date: `2026-05-21`

## Goal

Decode the `WifiStatus` returned by the now-working raw hwbinder
`IWifi.start()` transaction, so the next blocker can be classified before any
scan/connect/link-up work.

## Result

- Decision: `v568-iwifi-start-status-error`
- Pass: `True`
- Reason: `IWifi.start()` completed at the hwbinder transport layer but returned
  `WifiStatusCode.ERROR_UNKNOWN` with code `9`.
- Evidence: `tmp/wifi/v568-companion-dual-hal-wificond-iwifi-start-status`
- Helper: `a90_android_execns_probe v93`
- Helper SHA-256:
  `1e9e60c937de8930f87ea62849824d15ab0efba689da8b5fa26a3ebd83095902`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v93 was deployed to `/cache/bin/a90_android_execns_probe`.
- The live proof started only the bounded companion, service-manager, dual-HAL,
  CNSS, and `wificond` window.
- The proof decoded the `IWifi.start()` status reply only.
- The proof did not run supplicant, hostapd, scan/connect/link-up, credentials,
  DHCP, route changes, external ping, reboot, or boot partition writes.
- Post-run cleanup was safe and no Wi-Fi network device appeared.

## Live Evidence

```text
iwifi_start.service_token_wire=cstring
iwifi_start.service_retained=1
iwifi_start.start.reply.data_size=84
iwifi_start.start.reply.status_name=OK
iwifi_start.start.wifi_status.decoded=1
iwifi_start.start.wifi_status.code=9
iwifi_start.start.wifi_status.name=ERROR_UNKNOWN
iwifi_start.start.wifi_status.description_size=0
iwifi_start.start.wifi_status_code=9
iwifi_start.start.wifi_status_name=ERROR_UNKNOWN
iwifi_start.start_transaction_ok=0
iwifi_start.result=transaction-failed
wifi_companion_hal_order.surface_after_iwifi_start.wlan_count=0
wifi_companion_hal_order.surface_after_iwifi_start.phy_count=0
wifi_companion_hal_order.all_postflight_safe=1
```

Readiness marker counts remained blocked:

```text
qmi_server_connected=0
qrtr_modem_readiness=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
```

## Interpretation

V568 proves the current blocker is no longer raw hwbinder mechanics. The helper
can reach the Wi-Fi HAL and decode a valid HAL status, but the HAL reports
`ERROR_UNKNOWN` before any observed QRTR/QMI/BDF/WLFW readiness marker or
WLAN/PHY surface appears.

The next work should classify the missing runtime dependency around QRTR,
remote storage, TFTP, pd-mapper, CNSS, firmware path, and Android-vs-native
runtime state. Repeating scan/connect would be premature because no Wi-Fi link
surface exists yet.

## References

- AOSP `WifiStatus` and `WifiStatusCode`:
  `https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/types.hal`
- Android error mapping for binder status names:
  `https://android.googlesource.com/platform/system/core/+/refs/tags/platform-tools-35.0.2/libutils/binder/include/utils/Errors.h`
- AOSP `IWifi.start()` contract:
  `https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/IWifi.hal`

## Next Gate

V569 should be a bounded HAL `ERROR_UNKNOWN` dependency classifier. It should
compare Android and native runtime surfaces for QRTR sockets, QMI readiness,
firmware/BDF availability, `/data/vendor/wifi` state, companion process file
descriptors, and CNSS daemon logs before any Wi-Fi scan/connect attempt.
