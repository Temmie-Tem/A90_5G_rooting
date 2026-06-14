# Native Init V1753 WLAN-PD Firmware-request Diff

## Summary

- Cycle: `V1753`
- Type: host-only Android-good vs native firmware-request diff
- Decision: `v1753-firmware-not-requested-android-good-diff-pass`
- Label: `firmware-not-requested`
- Result: PASS
- Reason: Android-good tftp_server requests wlanmdsp.mbn, while the native V1736 service-manager route reaches the WLFW worker but never requests wlanmdsp
- Evidence: `tmp/wifi/v1753-wlan-pd-firmware-request-diff`

## Android-good Evidence

- Manifest: `tmp/wifi/v1753-android-good-wlan-pd-firmware-request/manifest.json`
- Decision/pass: `v1753-android-good-firmware-request-observed-rollback-pass` / `True`
- `wlanmdsp` request seen: `1`
- `wlanmdsp` line count: `21`
- Paths: `["/vendor/firmware_mnt/image/wlanmdsp.mbn", "/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn", "/vendor/firmware/wlanmdsp.mbn", "/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn"]`

## Native Baseline Evidence

- Manifest: `tmp/wifi/v1736-wlan-pd-timestamped-observer-handoff/manifest.json`
- Decision/pass: `v1736-wlfw-start-reached-downstream-block-rollback-pass` / `True`
- service-manager: `1`
- tftp running: `1`
- `wlfw_start` / `wlfw_service_request` / worker hits: `1` / `1` / `1`
- WLFW service 69 / indication QMI / capability QMI: `0` / `0` / `0`
- requested `wlanmdsp`: `0`
- firmware label: `firmware-not-requested`

## Fresh Native Attempt

- Present: `True`
- Decision/pass: `v1736-test-boot-flash-or-verify-failed` / `False`
- Rollback: `{'attempt': 'from-native', 'ok': True}`
- Note: fresh V1753 native run was a transport non-result if `pass=false`; it is recorded but excluded from the diff label.

## Android-good `wlanmdsp` Excerpt

```text
06-03 04:17:31.380  1684  2518 I tftp_server: pid=1684 tid=2518 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor
06-03 04:17:31.390  1684  2518 I tftp_server: pid=1684 tid=2518 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn]
06-03 04:17:31.409  1684  2523 I tftp_server: pid=1684 tid=2523 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor/firmware/
06-03 04:17:31.409  1684  2523 I tftp_server: pid=1684 tid=2523 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn]
06-03 04:17:31.411  1684  2542 I tftp_server: pid=1684 tid=2542 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor
06-03 04:17:31.411  1684  2542 I tftp_server: pid=1684 tid=2542 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn]
06-03 04:17:31.412  1684  2545 I tftp_server: pid=1684 tid=2545 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor/firmware/
06-03 04:17:31.412  1684  2545 I tftp_server: pid=1684 tid=2545 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn]
06-03 04:17:31.417  1684  2547 I tftp_server: pid=1684 tid=2547 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor/firmware/
06-03 04:17:31.417  1684  2547 I tftp_server: pid=1684 tid=2547 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn]
06-03 04:17:31.380  1684  2518 I tftp_server: pid=1684 tid=2518 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor
06-03 04:17:31.390  1684  2518 I tftp_server: pid=1684 tid=2518 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn]
06-03 04:17:31.409  1684  2523 I tftp_server: pid=1684 tid=2523 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor/firmware/
06-03 04:17:31.409  1684  2523 I tftp_server: pid=1684 tid=2523 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn]
06-03 04:17:31.411  1684  2542 I tftp_server: pid=1684 tid=2542 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor
06-03 04:17:31.411  1684  2542 I tftp_server: pid=1684 tid=2542 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn]
06-03 04:17:31.412  1684  2545 I tftp_server: pid=1684 tid=2545 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor/firmware/
06-03 04:17:31.412  1684  2545 I tftp_server: pid=1684 tid=2545 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn]
06-03 04:17:31.417  1684  2547 I tftp_server: pid=1684 tid=2547 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor/firmware/
06-03 04:17:31.417  1684  2547 I tftp_server: pid=1684 tid=2547 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn]
/vendor/firmware/wlanmdsp.mbn
```

## Interpretation

- Android-good proves the modem asks `tftp_server` for `wlanmdsp.mbn`, including vendor RFS paths under `/vendor/rfs/msm/mpss/readonly/vendor/...`.
- Native V1736 proves the service-manager route reaches `wlfw_service_request` and WLFW worker creation, with `tftp_server` running, but no `wlanmdsp` request appears.
- The next blocker is therefore above firmware serving in native: the modem-side WLAN-PD autoload/request trigger is missing.
- Stop here. Do not patch served paths, add PM/QCACLD/eSoC actors, issue restart-PD, start Wi-Fi HAL, scan/connect, use credentials, DHCP/routes, or external ping in this unit.

## Safety Scope

This diff script is host-only. The Android-good handoff used a temporary Magisk diagnostic module and rolled back to v724. The fresh native attempt rolled back to v724 but is not used as a label because transport did not become ready. This unit performs no new device contact, flash, reboot, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, or firmware/partition write.
