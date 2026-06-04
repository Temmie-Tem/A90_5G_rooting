# Native Init V2053 Pre-WLANMDSP Trigger Event Diff

## Summary

- Cycle: `V2053`
- Type: host-only Android-good vs native pre-`wlanmdsp` RRQ event comparison
- Decision: `v2053-android-rrq-after-wlfw-request-before-pd-up-native-skips-bootstrap-pass`
- Label: `android-rrq-after-wlfw-request-before-pd-up-native-skips-bootstrap`
- Result: `PASS`
- Reason: Android's first wlanmdsp RRQ follows cnss WLFW service request and precedes wlan_pd UP; native has the cnss request and wlan_pd UP but skips the server_check/ota/wlanmdsp bootstrap branch
- Evidence: `tmp/wifi/v2053-pre-wlanmdsp-trigger-event-diff`

## Direct Answer

- Android's first `wlanmdsp.mbn` RRQ is preceded by the `server_check.txt` WRQ / `ota_firewall/ruleset` RRQ bootstrap branch and then by `cnss-daemon` `wlfw_service_request` after the PerMgr modem vote.
- The first Android `wlanmdsp` RRQ is approximately `0.582` seconds after `wlfw_service_request` and approximately `0.311` seconds before `wlan_pd` UP, using the `wlfw_service_request` logcat-to-dmesg alignment.
- Therefore the RRQ is part of the WLAN-PD spawn/load sequence; it is not triggered by `wlan_pd` already being UP, WLFW service 69, BDF, or later `mcfg` traffic.
- Native reproduces the AP-side `wlfw_service_request` and reaches `wlan_pd` UP, but its TFTP branch has `server_check=0`, `ota_firewall=0`, `wlanmdsp=0`, and only later `mcfg` traffic.

## Android-Good Timeline

| event | time | delta_from_tftp_start_ms | line |
| --- | --- | --- | --- |
| tftp_start | 06-04 08:16:52.352 | 0.0 | 06-04 08:16:52.352 1660 1660 I tftp_server: Starting... |
| server_check_wrq | 06-04 08:16:52.726 | 374.0 | 06-04 08:16:52.726 1660 1808 I tftp_server: pid=1660 tid=1808 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/server_check.txt] : [/vendor/rfs/msm/mpss/rea… |
| ota_firewall_rrq | 06-04 08:16:52.733 | 381.0 | 06-04 08:16:52.733 1660 1811 I tftp_server: pid=1660 tid=1811 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/ota_firewall/ruleset] : [/vendor/rfs/msm/mpss… |
| wlfw_start | 06-04 08:16:53.763 | 1411.0 | 06-04 08:16:53.763 2120 2120 I cnss-daemon: wlfw_start: Starting |
| per_mgr_add_client | 06-04 08:16:53.766 | 1414.0 | 06-04 08:16:53.766 1588 1650 D PerMgrSrv: modem state: is on-line, add client cnss-daemon |
| per_mgr_vote | 06-04 08:16:53.768 | 1416.0 | 06-04 08:16:53.768 2120 2120 D PerMgrLib: cnss-daemon voting for modem |
| wlfw_service_request | 06-04 08:16:53.798 | 1446.0 | 06-04 08:16:53.798 2120 2208 I cnss-daemon: wlfw_service_request: Start the pthread: 0x0K |
| first_wlanmdsp_rrq | 06-04 08:16:54.380 | 2028.0 | 06-04 08:16:54.380 1660 2456 I tftp_server: pid=1660 tid=2456 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/ve… |
| first_mcfg | 06-04 08:17:02.618 | 10266.0 | 06-04 08:17:02.618 1660 4065 I tftp_server: pid=1660 tid=4065 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] : [/vendor/rfs/msm/mpss/readwrite/m… |
| wlfw_service_connected | 06-04 08:16:54.694 | 2342.0 | 06-04 08:16:54.694 2120 2208 I cnss-daemon: WLFW service connected |
| wlfw_cap_req | 06-04 08:16:54.829 | 2477.0 | 06-04 08:16:54.829 2120 2208 I cnss-daemon: wlfw_send_cap_req: chip_id: 0x30224, chip_family 0x4001, board_id: 0xff, soc_id: 0x40060000, fw_version: 0x3204038e, fw_build… |
| first_bdf | 06-04 08:16:54.847 | 2495.0 | 06-04 08:16:54.847 2120 2208 I cnss-daemon: wlfw_send_bdf_download_req: BDF file : regdb.bin |
| wlan_pd_up | 9.567253 | dmesg | [ 9.567253] [6: kworker/u16:6: 250] service-notifier: root_service_service_ind_cb: Indication received from msm/modem/wlan_pd, state: 0x1fffffff, trans-id: 1 |
| icnss_qmi_connected | 9.569576 | dmesg | [ 9.569576] [6: kworker/u16:3: 244] icnss_qmi: QMI Server Connected: state: 0x980 |
| dmesg_first_bdf | 9.722886 | dmesg | [ 9.722886] [3: sh: 2631] cnss-daemon wlfw_send_bdf_download_req: BDF file : regdb.bin |
| wlan0 | 14.866239 | dmesg | [ 14.866239] [6: kworker/u16:3: 244] dev : wlan0 : event : 16 |

## Native Timeline

| event | time | delta_from_wlfw_service_request_ms | line |
| --- | --- | --- | --- |
| wlfw_start | 6.699069 | -5.5 | cnss-daemon-622 [001] .... 6.699069: wlfw_start: (0x55696bec00) |
| wlfw_service_request | 6.704613 | 0.0 | cnss-daemon-633 [001] .... 6.704613: wlfw_service_request: (0x55696bd9fc) |
| first_tftp_server_log | 14.267000 | 7562.4 | monotonic_ms=14267 delta_ms=0 \x003\x02\xf3\xad\x83Z)\xf4x\x14\x04tftp_server\x00Initializing tftp_server RING buffer\x00 |
| first_server_check |  |  | monotonic_ms=0 delta_ms=0 |
| first_ota_firewall |  |  | monotonic_ms=0 delta_ms=0 |
| first_wlanmdsp |  |  | monotonic_ms=0 delta_ms=0 |
| first_mcfg | 15.755000 | 9050.4 | monotonic_ms=15755 delta_ms=0 \x00\x88\x02\xff\xad\x83Z\xd8>?8\x04tftp_server\x00pid=563 tid=648 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] … |
| wlfw_client_init_instance_retcheck | 7.933204 | 1228.6 | cnss-daemon-633 [001] .... 7.933204: wlfw_client_init_instance_retcheck: (0x55696bdaac) rc=0x0 |
| wlfw_send_ind_register_entry | 7.934353 | 1229.7 | cnss-daemon-633 [001] .... 7.934353: wlfw_send_ind_register_entry: (0x55696bf268) |
| wlfw_qmi_ind_cb_entry | 7.937857 | 1233.2 | cnss-daemon-647 [002] .... 7.937857: wlfw_qmi_ind_cb_entry: (0x55696be100) msg_id=0x2b payload_len=0x0 |
| wlfw_cap_qmi | 7.938000 | 1233.4 | cnss-daemon-633 [001] .... 7.938000: wlfw_cap_qmi: (0x55696bf460) |
| wlfw_bdf_entry | 7.982758 | 1278.1 | cnss-daemon-633 [001] .... 7.982758: wlfw_bdf_entry: (0x55696bf76c) bdf_type=0x4 |
| wlan_pd_up | 7.927901 | dmesg | [ 7.927901] [2: kworker/u16:3: 244] service-notifier: root_service_service_ind_cb: Indication received from msm/modem/wlan_pd, state: 0x1fffffff, trans-id: 1 |
| icnss_qmi_connected | 7.930474 | dmesg | [ 7.930474] [0: kworker/u16:1: 75] icnss_qmi: QMI Server Connected: state: 0x980 |
| wlan0 |  | dmesg |  |

## Native TFTP Counts

| datagrams | server_check | ota_firewall | wlanmdsp | mcfg |
| --- | --- | --- | --- | --- |
| 27 | 0 | 0 | 0 | 3 |

## Interpretation

- `mcfg` is downstream/noise for this gate: Android requests `wlanmdsp` before any `mcfg.tmp` line, while native's only TFTP payload is `mcfg` after the WLAN-PD edge.
- `ota_firewall/ruleset` completion is not a success prerequisite in Android-good because the captured `ota_firewall` reads return ENOENT, but the modem still proceeds to `wlanmdsp`.
- The nearest AP-visible predecessor is `wlfw_service_request`; because native already emits it, the missing condition is either TFTP-server readiness/registration at that exact pre-UP window or a modem-internal branch condition that selects the WLAN-PD bootstrap path.
- The next bounded unit should force Android-order readiness only: prove `tftp_server` is fully started/registered before `pm-service`/`cnss-daemon` vote, then look for `server_check -> ota_firewall -> wlanmdsp` before `wlan_pd` UP. Do not tune `mcfg.tmp` readback.

## Safety

This unit is host-only and reuses existing V1982/V2049 evidence. It performs no device contact, flash, reboot, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping, PMIC/GPIO/GDSC write, eSoC/PCIe action, platform bind/unbind, or partition write.
