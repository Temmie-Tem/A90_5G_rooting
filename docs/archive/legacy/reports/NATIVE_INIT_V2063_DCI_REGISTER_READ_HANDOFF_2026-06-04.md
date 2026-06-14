# Native Init V2063 DIAG DCI Register-Read Handoff

## Summary

- Cycle: `V2063`
- Decision: `v2063-diag-dci-register-read-no-payload-route-changed-rollback-pass`
- Label: `diag-dci-register-read-no-payload-route-changed`
- Pass: `True`
- Reason: DCI registration succeeded without payload, but the lower Wi-Fi route changed relative to V2059
- Evidence: `tmp/wifi/v2063-dci-register-read-handoff`
- Inner handoff: `tmp/wifi/v2063-dci-register-read-handoff/v2062-handoff/manifest.json`
- Comparator: `docs/reports/NATIVE_INIT_V2059_PERMGR_VOTE_FOCUSED_HANDOFF_2026-06-04.md` remains the PerMgr discriminator; V2059 showed cnss-daemon register/connect plus pm-service server acceptance succeeded with no `wlanmdsp` request.
- Route note: a `diag-dci-register-read-no-payload-route-changed` label means the DCI run is not a PerMgr-negative result; `cnss-daemon` exited before PerMgr registration, so this run only proves the register-only DCI path itself produced no payload.

## Matrix

| area | value | detail |
| --- | --- | --- |
| route | False | hook=True diag_safe=True |
| cnss_permgr | False | client=False peripheral=False server=False |
| diag_register | True | open=True supported=True proc=0 mask=0x1 rc=1 client=1 |
| diag_reads | 0 | records=4 bytes=2618 payload=0 bootstrap=4 other=0 eagain=0 errors=1 terminal_error=1 |
| diag_cleanup | 1 | deinit_rc=1001 errno=0 |
| tftp_branch |  | server_check=0 ota=0 mcfg=5 wlanmdsp=0 |
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
| focused_label | cnss-permgr-register-not-started |
| cnss_register_ret | none |
| cnss_connect_ret | none |
| pm_service | entry=0 match=0 add_client=0 success=0 |

## Branch

- If `diag-dci-register-read-payload-present-no-wlan0`, decode the captured DCI/user payload offline before adding any log/event masks.
- If `diag-dci-register-read-no-payload-no-wlanmdsp`, register-only DCI is insufficient; the next modem-internal visibility path is a bounded active DCI log/event stream-mask capture.
- If `diag-dci-register-read-no-payload-route-changed`, keep V2059 as the AP-side PerMgr answer and treat this run as a DCI visibility-only result, because the lower route did not match the focused PerMgr baseline.
- If `diag-dci-register-failed`, repair the DCI registration contract before any heavier logging-mode path.

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
- DIAG use was limited to a private rootfs `/dev/diag` char node plus `DIAG_IOCTL_DCI_SUPPORT`, `DIAG_IOCTL_DCI_REG`, nonblocking reads, and `DIAG_IOCTL_DCI_DEINIT`. No `DIAG_IOCTL_SWITCH_LOGGING`, DIAG write, log/event mask write, DCI stream config, passive DIAG replay, QMI send, AP-side strace, boot-time QRTR matrix, or ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2062 test-boot flash-handoff, namespace-local fallback readonly/readwrite RFS bridges, namespace-local persist-RFS tmpfs mirrors, private tmp-root `/dev/socket/logdw`, private tmp-root `/dev/diag`, tracefs uprobes, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
