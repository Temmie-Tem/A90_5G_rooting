# Native Init V2065 DIAG DCI Canary-Mask Handoff

## Summary

- Cycle: `V2065`
- Decision: `v2065-dci-canary-mask-set-clear-ok-rollback-pass`
- Label: `dci-canary-mask-set-clear-ok`
- Pass: `True`
- Reason: bounded DCI data writes can set, query, clear, and re-query one log/event canary without logging-mode switch or broad masks
- Evidence: `tmp/wifi/v2065-dci-canary-mask-handoff`
- Inner handoff: `tmp/wifi/v2065-dci-canary-mask-handoff/v2064-handoff/manifest.json`
- Comparator: V2059 remains the AP-side PerMgr answer; V2065 only validates whether a bounded active DCI canary mask path is viable before selecting modem/WLAN-specific masks.

## Matrix

| area | value | detail |
| --- | --- | --- |
| route | True | hook=True diag_safe=True canary_safe=True |
| diag_register | True | open=True proc=0 mask=0x1 rc=1 client=1 |
| canary_writes | True | attempts=4 success=4 errors=0 log_set_rc=1001 event_set_rc=1001 log_clear_rc=1001 event_clear_rc=1001 |
| canary_status | True | pre=log:0 event:0 set=log:1 event:1 clear=log:0 event:0 |
| health |  | pre_logs=0 pre_events=0 post_logs=0 post_events=0 |
| diag_reads | 0 | records=4 bytes=2618 payload=0 bootstrap=4 other=0 errors=1 terminal_error=1 |
| tftp_branch |  | server_check=0 ota=0 mcfg=7 wlanmdsp=0 |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 |

## DIAG Support Detail

| proc | rc | errno | support_mask | nonzero |
| --- | --- | --- | --- | --- |
| 0 | 1001 | 0 | 0x1 | 1 |
| 1 | 1001 | 0 | 0x0 | 0 |
| 2 | -1 | 5 | 0x0 | 0 |
| 3 | -1 | 5 | 0x0 | 0 |
| 4 | -1 | 5 | 0x0 | 0 |
| 5 | -1 | 5 | 0x0 | 0 |
| 6 | -1 | 5 | 0x0 | 0 |
| 7 | -1 | 5 | 0x0 | 0 |

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
| cnss_register_ret | cnss-daemon-623   [001] ....     8.114352: pm_init_pm_client_register_retcheck: (0x5583c86628) rc=0x0 |
| cnss_connect_ret | cnss-daemon-623   [001] ....     8.115400: pm_init_pm_client_connect_retcheck: (0x5583c86654) rc=0x0 |
| pm_service | entry=1 match=1 add_client=1 success=1 |

## Branch

- If `dci-canary-mask-set-clear-ok`, the next step is a targeted active DCI mask list for modem/WLAN PD producer events, still bounded and rollbackable.
- If `dci-canary-mask-write-failed` or `dci-canary-mask-status-mismatch`, repair the DCI mask ABI before selecting any modem/WLAN-specific masks.
- If `dci-canary-mask-register-failed`, repair the DCI registration contract before any heavier logging-mode path.

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
- DIAG use was limited to a private rootfs `/dev/diag` char node, `DIAG_IOCTL_DCI_SUPPORT`, `DIAG_IOCTL_DCI_REG`, nonblocking reads, `DIAG_IOCTL_DCI_DEINIT`, status queries, and one DCI data canary sequence that set/query/cleared exactly log code `0x0000` and event id `0`.
- No `DIAG_IOCTL_SWITCH_LOGGING`, broad log/event mask, DCI stream config, passive DIAG replay, QMI send, AP-side strace, boot-time QRTR matrix, or ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2064 test-boot flash-handoff, namespace-local fallback readonly/readwrite RFS bridges, namespace-local persist-RFS tmpfs mirrors, private tmp-root `/dev/socket/logdw`, private tmp-root `/dev/diag`, tracefs uprobes, bounded DCI canary mask set/clear, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
