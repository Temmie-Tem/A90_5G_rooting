# Native Init V2011 Post-Cal TFTP Sockaddr Handoff

## Summary

- Cycle: `V2011`
- Decision: `v2011-post-cal-tftp-sockaddr-qrtr-inbound-no-tokenized-tftp-rollback-pass`
- Label: `post-cal-tftp-sockaddr-qrtr-inbound-no-tokenized-tftp`
- Pass: `True`
- Reason: stock tftp_server received QRTR-sourced inbound payloads without path tokens; decode that binary protocol before assigning zero tftp
- Evidence: `tmp/wifi/v2011-post-cal-tftp-sockaddr-handoff`
- Inner handoff: `tmp/wifi/v2011-post-cal-tftp-sockaddr-handoff/v2010-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | post-cal-tftp-sockaddr-qrtr-inbound-no-tokenized-tftp | stock tftp_server received QRTR-sourced inbound payloads without path tokens; decode that binary protocol before assigning zero tftp |
| helper | True | a90_android_execns_probe v374 |
| route | True | service74=True service180=True pm_open=False holder=True |
| bridges |  | readonly=True readwrite=True |
| cascade |  | wlan_pd=1 icnss_qmi=1 wlfw69=0 fw_ready=0 wlan0=0 |
| tftp_summary |  | requested_any=0 server_check=0 wlanmdsp=0 pd_load=0 summary_wlanmdsp=0 |
| tftp_trace | True | compiled=1 attach_rc=0 detach_rc=0 records=22 stops=45 ms=6009 truncated=0 |
| tftp_payloads | False | recv_payload=20 send_payload=0 qipcrtr=20 sources={'AF_QIPCRTR': 20} nodes={'1': 20} ports={'4294967294': 20} |
| tftp_tokens | {'server_check': 0, 'ota_firewall': 0, 'mcfg': 0, 'mbn_hw': 0, 'wlanmdsp': 0, 'modem': 0} | summary server_check=0 mcfg=0 mbn_hw=0 ota=0 wlanmdsp=0 |
| cap_bdf_cal |  | cap=0x0 bdf=0x0 cal=0x0 worker_cal=0x0 |
| indication |  | cb_hits=2 first_msg=0x2b len=0x0 handle_type= fw_status= |

## First TFTP Source Records

- `record_001 ret=20 fd=socket:[15521] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_002 ret=20 fd=socket:[15522] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_003 ret=20 fd=socket:[15523] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_004 ret=20 fd=socket:[15524] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_005 ret=20 fd=socket:[15525] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_006 ret=20 fd=socket:[15526] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_007 ret=20 fd=socket:[15527] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_008 ret=20 fd=socket:[15528] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_009 ret=20 fd=socket:[15529] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_010 ret=20 fd=socket:[15530] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_012 ret=20 fd=socket:[15521] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`
- `record_013 ret=20 fd=socket:[15522] family=AF_QIPCRTR node=1 port=4294967294 socklen=12/12`

## First TFTP Trace Records

- `record_000 ppoll ret=10`
- `record_001 recvfrom ret=20 socket:[15521]`
- `record_002 recvfrom ret=20 socket:[15522]`
- `record_003 recvfrom ret=20 socket:[15523]`
- `record_004 recvfrom ret=20 socket:[15524]`
- `record_005 recvfrom ret=20 socket:[15525]`
- `record_006 recvfrom ret=20 socket:[15526]`
- `record_007 recvfrom ret=20 socket:[15527]`
- `record_008 recvfrom ret=20 socket:[15528]`
- `record_009 recvfrom ret=20 socket:[15529]`
- `record_010 recvfrom ret=20 socket:[15530]`
- `record_011 ppoll ret=10`

## First Payload Words

- `record_001 0x6 0x0 0x62 0x0 0x0`
- `record_002 0x6 0x0 0x62 0x0 0x0`
- `record_003 0x6 0x0 0x62 0x0 0x0`
- `record_004 0x6 0x0 0x62 0x0 0x0`
- `record_005 0x6 0x0 0x62 0x0 0x0`
- `record_006 0x6 0x0 0x62 0x0 0x0`
- `record_007 0x6 0x0 0x62 0x0 0x0`
- `record_008 0x6 0x0 0x62 0x0 0x0`

## Tail Events

| event | hits | fetch | first |
| --- | --- | --- | --- |
| wlfw_cal_report_entry | 1 | none | cnss-daemon-636   [001] ....     8.050871: wlfw_cal_report_entry: (0x556c91d5a0) |
| wlfw_cal_report_send_ret | 1 | send_rc=%x0 qmi_result=%x4 qmi_error=%x5 | cnss-daemon-636   [001] ....     8.051223: wlfw_cal_report_send_ret: (0x556c91d6dc) send_rc=0x0 qmi_result=0x0 qmi_error=0xffffffff |
| wlfw_cal_report_error_branch | 0 | send_rc=%x0 | none |
| wlfw_cal_report_success_branch | 1 | qmi_result=%x4 qmi_error=%x5 | cnss-daemon-636   [001] ....     8.051231: wlfw_cal_report_success_branch: (0x556c91d71c) qmi_result=0x0 qmi_error=0x0 |
| wlfw_cal_report_return | 1 | rc=%x19 | cnss-daemon-636   [001] ....     8.051271: wlfw_cal_report_return: (0x556c91d750) rc=0x0 |
| dms_get_wlan_address_entry | 1 | none | cnss-daemon-635   [003] ....     7.809727: dms_get_wlan_address_entry: (0x556c91c544) |
| dms_get_wlan_address_send_ret | 1 | send_rc=%x0 qmi_result=%x3 | cnss-daemon-635   [001] ....     7.825372: dms_get_wlan_address_send_ret: (0x556c91c5a0) send_rc=0x0 qmi_result=0xd |
| dms_get_wlan_address_valid_mac | 0 | none | none |
| dms_get_wlan_address_return | 1 | rc=%x19 | cnss-daemon-635   [003] ....     7.838221: dms_get_wlan_address_return: (0x556c91c670) rc=0xffffffff |
| dms_service_request_init_ret | 1 | rc=%x0 | cnss-daemon-635   [003] ....     7.809722: dms_service_request_init_ret: (0x556c91c92c) rc=0x0 |
| dms_service_request_cond_wait | 0 | none | none |
| dms_service_request_send_ret | 0 | send_rc=%x0 qmi_result=%x3 qmi_error=%x4 | none |
| dms_service_request_success_branch | 0 | qmi_result=%x3 qmi_error=%x4 | none |
| wlan_send_status_entry | 0 | is_on=%x0 cookie=%x1 | none |
| wlan_send_status_send_ret | 0 | send_rc=%x0 qmi_result=%x3 | none |
| wlan_send_status_return | 0 | rc=%x19 | none |
| wlan_send_version_entry | 0 | none | none |
| wlan_send_version_open_success | 0 | none | none |
| wlan_send_version_not_found | 0 | none | none |
| wlan_send_version_send_ret | 0 | send_rc=%x0 qmi_result=%x4 | none |
| wlan_send_version_return | 0 | rc=%x23 | none |

## Indication Events

| event | hits | fetch | first |
| --- | --- | --- | --- |
| wlfw_worker_second_bdf_branch | 1 | bdf_rc=%x19 | cnss-daemon-636   [001] ....     8.050863: wlfw_worker_second_bdf_branch: (0x556c91bc98) bdf_rc=0x0 |
| wlfw_worker_cal_only_call | 1 | none | cnss-daemon-636   [001] ....     8.050868: wlfw_worker_cal_only_call: (0x556c91bfe0) |
| wlfw_worker_cal_only_retcheck | 1 | rc=%x0 | cnss-daemon-636   [001] ....     8.051278: wlfw_worker_cal_only_retcheck: (0x556c91bfe4) rc=0x0 |
| wlfw_worker_done_signal | 1 | none | cnss-daemon-636   [001] ....     8.051281: wlfw_worker_done_signal: (0x556c91bff8) |
| wlfw_worker_post_done_wait | 1 | none | cnss-daemon-636   [001] ....     8.051316: wlfw_worker_post_done_wait: (0x556c91c070) |
| wlfw_worker_handle_ind_call | 0 | none | none |
| wlfw_qmi_ind_cb_entry | 2 | msg_id=%x1 payload_len=%x3 | cnss-daemon-648   [000] ....     7.998210: wlfw_qmi_ind_cb_entry: (0x556c91c100) msg_id=0x2b payload_len=0x0 |
| wlfw_qmi_ind_msg_unknown | 0 | msg_id=%x21 | none |
| wlfw_qmi_ind_decode_0x28_ok | 0 | none | none |
| wlfw_qmi_ind_decode_0x2a_ok | 0 | none | none |
| wlfw_qmi_ind_decode_0x41_ok | 0 | none | none |
| wlfw_qmi_ind_fw_mem_flag | 1 | msg_id=%x21 | cnss-daemon-648   [000] ....     7.998261: wlfw_qmi_ind_fw_mem_flag: (0x556c91c2f0) msg_id=0x2b |
| wlfw_qmi_ind_msa_flag | 0 | msg_id=%x21 | none |
| wlfw_qmi_ind_queue_link | 0 | none | none |
| wlfw_qmi_ind_cond_signal | 1 | none | cnss-daemon-648   [000] ....     7.998306: wlfw_qmi_ind_cond_signal: (0x556c91c450) |
| wlfw_handle_ind_entry | 0 | none | none |
| wlfw_handle_ind_type | 0 | ind_type=%x3 | none |
| wlfw_handle_ind_type_0x28 | 0 | fw_status=%x4 | none |
| wlfw_handle_ind_type_0x2a | 0 | arg0=%x4 arg1=%x5 | none |
| wlfw_handle_ind_type_0x41 | 0 | arg0=%x4 arg1=%x5 | none |

## Branch

- `post-cal-tftp-sockaddr-wlan0-progress`: real interface appeared; keep HAL/scan/connect gated for a separate unit.
- `post-cal-tftp-sockaddr-wlanmdsp-request-progress`: request/load edge appeared with cnss-daemon running; chase downstream cascade only.
- `post-cal-tftp-sockaddr-server-check-or-mcfg-no-wlanmdsp`: early modem tftp exists but no wlanmdsp; WLAN PD branch is modem-internal.
- `post-cal-tftp-sockaddr-qrtr-inbound-no-tokenized-tftp`: tftp_server sees QRTR binary control traffic; decode that protocol before calling zero tftp.
- `post-cal-tftp-sockaddr-zero-request`: no modem tftp reached stock tftp_server despite both bridges and downstream consumers.

## Steps

- `pre-version` rc `0` ok `True` evidence `host/pre-version.txt`
- `pre-selftest` rc `0` ok `True` evidence `host/pre-selftest.txt`
- `pre-flags` rc `0` ok `True` evidence `host/pre-flags.txt`
- `arm-clean-dsp-flag` rc `0` ok `True` evidence `host/arm-clean-dsp-flag.txt`
- `cleanup-leftover-clean-dsp-flag` rc `0` ok `True` evidence `host/cleanup-leftover-clean-dsp-flag.txt`
- `post-selftest` rc `0` ok `True` evidence `host/post-selftest.txt`
- `post-status` rc `0` ok `True` evidence `host/post-status.txt`
- `post-flags` rc `0` ok `True` evidence `host/post-flags.txt`

## Safety

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was used.
- No rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, or QMI payload send was run.
- The only ptrace was the bounded single-child syscall trace of stock `tftp_server`; no AP-side multi-strace was run.
- No direct `/dev/subsys_esoc0` open/control, forced RC1/case, PMIC/GPIO/GDSC/regulator, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2010 test-boot flash-handoff, namespace-local RFS tmpfs/symlink bridges, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
