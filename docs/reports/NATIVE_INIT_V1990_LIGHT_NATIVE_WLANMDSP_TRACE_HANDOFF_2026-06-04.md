# Native Init V1990 Light Native Wlanmdsp Trace Handoff

## Summary

- Cycle: `V1990`
- Decision: `v1990-native-wlanmdsp-not-requested-light-rollback-pass`
- Label: `native-wlanmdsp-not-requested-light`
- Pass: `True`
- Reason: native reproduced current AP-side PM/CNSS prerequisites, but the internal modem never requested wlanmdsp.mbn
- Evidence: `tmp/wifi/v1990-light-native-wlanmdsp-trace-handoff`
- Inner handoff: `tmp/wifi/v1990-light-native-wlanmdsp-trace-handoff/v1989-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | native-wlanmdsp-not-requested-light | native reproduced current AP-side PM/CNSS prerequisites, but the internal modem never requested wlanmdsp.mbn |
| light_observer | True | servloc=0 servnotif=0 qrtr_send=0 result=blocked |
| combined_prereq | True | service74=True service180=True pm_open=True holder=True |
| wlanmdsp_request | False | field=False mbn_lines=4 tftp_lines=0 failures=0 |
| wlanmdsp_serve_load | False | served_nonzero=False pil_load=0 wlan_pd_up=0 wlfw69=0 wlan0=0 |
| degraded_external_watch | 0 | pcie_initialized/mhi_enable/esoc0_boot_failed/LTSSM only; no eSoC/PCIe action was taken |
| android_v1982 | 1 | wlan_pd=9.567253 BDF=9.722886 wlan0=14.866239 lines=10 |

## First Native Wlanmdsp Lines

- `none`

## First Native Load/UP Lines

- `none`

## Degraded External Watch

- `none`

## Android Comparator

- Report: `docs/reports/NATIVE_INIT_V1982_V1753_MINIMAL_ANDROID_GOOD_BASELINE_RERUN_2026-06-04.md`
- Timeline: WLAN-PD UP `9.567253`, BDF `9.722886`, wlan0 `14.866239`.
- Request evidence: requested_wlanmdsp `1`, wlanmdsp line count `10`.
- First Android line: `06-04 08:16:54.380  1660  2456 I tftp_server: pid=1660 tid=2456 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor`

## Interpretation

- If label is `native-wlanmdsp-not-requested-light`, the remaining wall is before the tftp request: the internal modem never advances to the WLAN PD code-image request stage.
- If label is `native-wlanmdsp-request-serve-failed`, the next bounded target is the native tftp/rfs served path for `wlanmdsp.mbn`.
- If label is `native-wlanmdsp-requested-served-pd-still-down`, the target moves deeper inside modem-side PD load/bring-up and should escalate to modem-side DIAG rather than more AP-side strace/QRTR matrix.

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
- No rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, or service-notifier listener was run in the V1989 init argv.
- No direct `/dev/subsys_esoc0` open/control, forced RC1/case, PMIC/GPIO/GDSC/regulator, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V1989 test-boot flash-handoff, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
