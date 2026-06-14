# Native Init V2085 Macloader Pre-CNSS Handoff

## Summary

- Cycle: `V2085`
- Decision: `v2085-macloader-pre-cnss-no-mac-no-tftp-bootstrap-rollback-pass`
- Label: `macloader-pre-cnss-no-mac-no-tftp-bootstrap`
- Pass: `True`
- Reason: macloader was observable, but no MAC assignment or tftp bootstrap followed
- Evidence: `tmp/wifi/v2085-macloader-pre-cnss-handoff`
- Inner handoff: `tmp/wifi/v2085-macloader-pre-cnss-handoff/v2084-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| macloader_route | True | hook=True mac_enabled=True mac_ready=True |
| macloader | True | mac_assigned=False loading_driver=0 boot_wlan_log=0 |
| tftp | False | server_check=0 ota=0 mcfg=5 wlanmdsp=0 fallback=0 |
| kernel_surface | 1 | dev_wlan=0 qcwlanstate=0 wlan0=0 |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 |
| rollback | True | post-selftest and post-status succeeded after rollback |

## Macloader Gate

| field | value |
| --- | --- |
| enabled | 1 |
| active_driver_start | 1 |
| boot_wlan_write_expected | 1 |
| qcwlanstate_write | 0 |
| observable | 1 |
| ready | 1 |
| child_exit_code | 0 |
| child_signal | 0 |
| mac_assigned | 0 |
| loading_driver | 0 |
| qcwlan_retry_log | 0 |

## Interpretation

- V2085 is the first native lower-window route that intentionally runs Android's `macloader` before `cnss-daemon` while retaining the RFS bridges, PerMgr/WLFW route, and light observer.
- If `server_check`/`wlanmdsp` appears, macloader is part of the missing AP-side trigger chain and the next gate is downstream FW-ready/wlan0.
- If MAC assignment appears but TFTP bootstrap remains absent, the remaining blocker is after AP-side macloader and before modem selection of the WLAN-PD firmware branch.
- If macloader is not observable, repair the macloader execution contract before re-classifying the producer gate.
- Observed V2085 result: `macloader` has the Android identity/domain/caps and stays observable, but no `boot_wlan`/driver-load/MAC-assignment log appears; the next discriminator is the `macloader` precondition/stall point, not PerMgr, RIL, TFTP registration, or SDX50M.

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

- No Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, credentials, DHCP/routes, or external ping was used.
- No passive DIAG, active DIAG mask/log-mode, rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, QMI payload send, or `tftp_server` ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2084 test-boot flash-handoff, namespace-local RFS bridges/tmpfs mirrors, private tmp-root `/dev/socket/logdw`, tracefs uprobes, Android-parity `macloader` driver-start action, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
