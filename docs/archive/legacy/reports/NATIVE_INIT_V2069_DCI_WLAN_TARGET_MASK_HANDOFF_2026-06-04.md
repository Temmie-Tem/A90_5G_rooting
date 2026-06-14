# Native Init V2069 DIAG DCI WLAN Target-Mask Handoff

## Summary

- Cycle: `V2069`
- Decision: `v2069-dci-wlan-target-mask-no-payload-no-wlanmdsp-rollback-pass`
- Label: `dci-wlan-target-mask-no-payload-no-wlanmdsp`
- Pass: `True`
- Reason: bounded WLAN target masks were active, but no DCI payload records and no wlanmdsp request appeared
- Evidence: `tmp/wifi/v2069-dci-wlan-target-mask-handoff`
- Inner handoff: `tmp/wifi/v2069-dci-wlan-target-mask-handoff/v2068-handoff/manifest.json`
- Comparator: V2059 closed AP-side PerMgr register/vote; V2069 tests whether bounded WLAN-specific DCI masks expose modem/WLAN producer payload without switching DIAG logging mode.

## Matrix

| area | value | detail |
| --- | --- | --- |
| route | True | hook=True diag_safe=True target_safe=True |
| diag_register | True | open=True proc=0 mask=0x1 rc=1 client=1 |
| target_set | True | attempts=6 success=6 errors=0 log_set=3/3 event_set=3/3 |
| target_clear | True | attempts=6 success=6 errors=0 log_still_set=0 event_still_set=0 completed=1 |
| health |  | pre_logs=0 post_logs=0 delta_logs=0 pre_events=0 post_events=0 delta_events=0 |
| diag_reads | 0 | records=4 bytes=2618 payload=0 bootstrap=4 other=0 errors=1 terminal_error=1 |
| tftp_branch |  | server_check=0 ota=0 mcfg=5 wlanmdsp=0 |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 |

## Target Logs

| idx | name | code | pre | set_rc | set | clear_rc | clear |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | LOG_WLAN_PKT_LOG_INFO_C | 0x18e0 | 0 | 1001 | 1 | 1001 | 0 |
| 1 | LOG_WLAN_COLD_BOOT_CAL_DATA_C | 0x1a18 | 0 | 1001 | 1 | 1001 | 0 |
| 2 | LOG_WLAN_DP_PROTO_PKT_INFO_C | 0x1a1e | 0 | 1001 | 1 | 1001 | 0 |

## Target Events

| idx | name | event_id | pre | set_rc | set | clear_rc | clear |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | EVENT_WLAN_BRINGUP_STATUS | 0x680 | 0 | 1001 | 1 | 1001 | 0 |
| 1 | EVENT_WLAN_LOG_COMPLETE | 0xaa7 | 0 | 1001 | 1 | 1001 | 0 |
| 2 | EVENT_WLAN_STATUS_V2 | 0xab3 | 0 | 1001 | 1 | 1001 | 0 |

## DIAG Read Samples

| idx | bytes | type | name | prefix_hex |
| --- | --- | --- | --- | --- |
| 0 | 4 | 0x1 | MSG_MASKS_TYPE | 01000000 |
| 1 | 517 | 0x4 | EVENT_MASKS_TYPE | 0400000000000000000000000000000000000000000000000000000000000000 |
| 2 | 1577 | 0x2 | LOG_MASKS_TYPE | 02000000000000000001e80c0000000000000000000000000000000000000000 |
| 3 | 520 | 0x200 | DCI_EVENT_MASKS_TYPE | 0002000001000000000000000000000000000000000000000000000000000000 |

## PerMgr Anchor

| field | value |
| --- | --- |
| focused_label | cnss-permgr-register-connect-server-accepted |
| cnss_register_ret | cnss-daemon-621   [001] ....     8.152068: pm_init_pm_client_register_retcheck: (0x5563739628) rc=0x0 |
| cnss_connect_ret | cnss-daemon-621   [001] ....     8.153129: pm_init_pm_client_connect_retcheck: (0x5563739654) rc=0x0 |
| pm_service | entry=1 match=1 add_client=1 success=1 |

## Branch

- If `dci-wlan-target-mask-payload-seen-no-wlanmdsp`, decode the DCI samples and choose a narrower modem-side trace point.
- If `dci-wlan-target-mask-no-payload-no-wlanmdsp`, mask-only DCI without `DIAG_IOCTL_SWITCH_LOGGING` still does not expose the producer; the next modem-side step is an explicit logging-mode/mask design gate or structured Frida/QMI tracing.
- If `dci-wlan-target-mask-wlanmdsp-requested`, chase the normal downstream cascade to BDF, FW-ready, and `wlan0`.

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
- DIAG use was limited to a private rootfs `/dev/diag` char node, `DIAG_IOCTL_DCI_SUPPORT`, `DIAG_IOCTL_DCI_REG`, nonblocking reads, `DIAG_IOCTL_DCI_DEINIT`, status queries, and exactly three WLAN log masks plus three WLAN event masks set during the lower window and cleared during cleanup.
- No `DIAG_IOCTL_SWITCH_LOGGING`, broad log/event mask, DCI stream config, passive DIAG replay, QMI send, AP-side strace, boot-time QRTR matrix, or ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2068 test-boot flash-handoff, namespace-local fallback readonly/readwrite RFS bridges, namespace-local persist-RFS tmpfs mirrors, private tmp-root `/dev/socket/logdw`, private tmp-root `/dev/diag`, tracefs uprobes, bounded DCI WLAN target masks, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
