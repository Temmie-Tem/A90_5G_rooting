# Native Init V2061 DIAG Query-Only Handoff

## Summary

- Cycle: `V2061`
- Decision: `v2061-diag-dci-support-present-no-wlanmdsp-rollback-pass`
- Label: `diag-dci-support-present-no-wlanmdsp`
- Pass: `True`
- Reason: query-only DIAG reached DCI support successfully while PerMgr still succeeded and native still made no wlanmdsp request
- Evidence: `tmp/wifi/v2061-diag-query-only-handoff`
- Inner handoff: `tmp/wifi/v2061-diag-query-only-handoff/v2060-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| route | True | hook=True diag_safe=True |
| cnss_permgr | True | client=True peripheral=True server=True |
| diag_query | True | open=True attempts=8 success=2 failures=6 |
| diag_dci | True | support_nonzero=1 first_proc=0 first_mask=0x3 |
| tftp_branch |  | server_check=0 ota=0 mcfg=7 wlanmdsp=0 |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 |

## DIAG Query Detail

| proc | rc | errno | support_mask | nonzero |
| --- | --- | --- | --- | --- |
| 0 | 1001 | 0 | 0x3 | 1 |
| 1 | 1001 | 0 | 0x0 | 0 |
| 2 | -1 | 5 | 0x0 | 0 |
| 3 | -1 | 5 | 0x0 | 0 |
| 4 | -1 | 5 | 0x0 | 0 |
| 5 | -1 | 5 | 0x0 | 0 |
| 6 | -1 | 5 | 0x0 | 0 |
| 7 | -1 | 5 | 0x0 | 0 |

## PerMgr Anchor

| field | value |
| --- | --- |
| focused_label | cnss-permgr-register-connect-server-accepted |
| cnss_register_ret | cnss-daemon-623   [000] ....     8.104652: pm_init_pm_client_register_retcheck: (0x556a428628) rc=0x0 |
| cnss_connect_ret | cnss-daemon-623   [000] ....     8.105699: pm_init_pm_client_connect_retcheck: (0x556a428654) rc=0x0 |
| pm_service | entry=1 match=1 add_client=1 success=1 |

## Branch

- If `diag-dci-support-present-no-wlanmdsp`, a bounded active DIAG DCI/log/event-mask capture is technically reachable and is the next modem-internal visibility path; query-only evidence still cannot show modem payloads by itself.
- If `diag-dci-support-query-no-supported-proc`, the next live DIAG route likely needs the heavier logging-mode/mask path rather than DCI support.
- Keep the V2059 AP-side conclusion intact when PerMgr remains successful and TFTP `wlanmdsp=0`: cnss PerMgr register/vote is not the missing WLAN image-request trigger.

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
- DIAG use was limited to a private rootfs `/dev/diag` char node plus `DIAG_IOCTL_DCI_SUPPORT` queries. No `DIAG_IOCTL_SWITCH_LOGGING`, DIAG write, log/event mask write, DCI stream config, passive DIAG replay, QMI send, AP-side strace, boot-time QRTR matrix, or ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2060 test-boot flash-handoff, namespace-local fallback readonly/readwrite RFS bridges, namespace-local persist-RFS tmpfs mirrors, private tmp-root `/dev/socket/logdw`, private tmp-root `/dev/diag`, tracefs uprobes, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
